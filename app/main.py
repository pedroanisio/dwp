from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import Dict, Any
import os
import json

from .core.plugin_manager import PluginManager
from .models.plugin import PluginInput
from .models.response import PluginListResponse, PluginExecutionResponse

# Initialize FastAPI app
app = FastAPI(
    title="Plugin System Web Application",
    description="A FastAPI + Pydantic web application with dynamic plugin system",
    version="1.0.0"
)

# Initialize plugin manager
plugin_manager = PluginManager()

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")

# Add custom Jinja2 filters
def tojsonpretty(value):
    return json.dumps(value, indent=2, ensure_ascii=False)

templates.env.filters['tojsonpretty'] = tojsonpretty

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage showing available plugins"""
    plugins = plugin_manager.get_all_plugins()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "plugins": plugins
    })


@app.get("/how-to", response_class=HTMLResponse)
async def how_to_page(request: Request):
    """How-to page for building and testing plugins"""
    return templates.TemplateResponse("how-to.html", {"request": request})


@app.get("/api/plugins", response_model=PluginListResponse)
async def get_plugins():
    """API endpoint to get all available plugins"""
    plugins = plugin_manager.get_all_plugins()
    return PluginListResponse(success=True, plugins=plugins)


@app.get("/plugin/{plugin_id}", response_class=HTMLResponse)
async def plugin_page(request: Request, plugin_id: str):
    """Plugin interaction page"""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return templates.TemplateResponse("plugin.html", {
        "request": request,
        "plugin": plugin
    })


@app.post("/api/plugin/{plugin_id}/execute")
async def execute_plugin_api(plugin_id: str, request: Request, input_file: UploadFile = File(None)):
    """API endpoint to execute a plugin"""
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        if input_file:
            data["input_file"] = {
                "filename": input_file.filename,
                "content": await input_file.read()
            }

        plugin_input = PluginInput(plugin_id=plugin_id, data=data)
        result = plugin_manager.execute_plugin(plugin_input)

        if result.success and result.file_data:
            return FileResponse(
                path=result.file_data["file_path"],
                filename=result.file_data["file_name"],
                media_type="application/octet-stream"
            )
        elif not result.success:
             return JSONResponse(status_code=400, content=result.dict())

        return result

    except Exception as e:
        return PluginExecutionResponse(
            success=False,
            plugin_id=plugin_id,
            error=str(e)
        )


@app.post("/plugin/{plugin_id}/execute", response_class=HTMLResponse)
async def execute_plugin_web(request: Request, plugin_id: str, input_file: UploadFile = File(None)):
    """Web interface for plugin execution"""
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        if input_file:
            data["input_file"] = {
                "filename": input_file.filename,
                "content": await input_file.read()
            }

        plugin_input = PluginInput(plugin_id=plugin_id, data=data)
        result = plugin_manager.execute_plugin(plugin_input)

        if result.success and result.file_data:
            return FileResponse(
                path=result.file_data["file_path"],
                filename=result.file_data["file_name"],
                media_type="application/octet-stream"
            )

        plugin = plugin_manager.get_plugin(plugin_id)
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "plugin": plugin,
            "result": result,
            "input_data": data
        })
    except Exception as e:
        plugin = plugin_manager.get_plugin(plugin_id)
        error_result = PluginExecutionResponse(
            success=False,
            plugin_id=plugin_id,
            error=str(e)
        )
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "plugin": plugin,
            "result": error_result,
            "input_data": {}
        })


@app.get("/api/plugin/{plugin_id}")
async def get_plugin_info(plugin_id: str):
    """Get information about a specific plugin"""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return {"success": True, "plugin": plugin}


@app.post("/api/refresh-plugins")
async def refresh_plugins():
    """Refresh the plugin list"""
    plugin_manager.refresh_plugins()
    plugins = plugin_manager.get_all_plugins()
    return {"success": True, "message": "Plugins refreshed", "count": len(plugins)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 