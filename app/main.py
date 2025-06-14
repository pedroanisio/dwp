from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import Dict, Any
import os
import json

from .core.plugin_manager import PluginManager
from .core.chain_manager import ChainManager
from .models.plugin import PluginInput
from .models.response import PluginListResponse, PluginExecutionResponse
from .models.chain import ChainDefinition, ChainExecutionResult

# Initialize FastAPI app
app = FastAPI(
    title="Neural Plugin System with Chain Builder",
    description="A FastAPI + Pydantic web application with dynamic plugin system and visual chain builder",
    version="2.0.0"
)

# Initialize managers
plugin_manager = PluginManager()
chain_manager = ChainManager(plugin_manager)

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


@app.get("/api/plugin-compliance")
async def check_plugin_compliance():
    """
    Check plugin compliance with the rule: ALL PLUGINS MUST DEFINE PYDANTIC RESPONSE MODELS
    
    Returns information about which plugins are compliant and which need to be updated.
    """
    all_plugins = plugin_manager.get_all_plugins()
    non_compliant = plugin_manager.get_non_compliant_plugins()
    
    compliant_plugins = []
    for plugin in all_plugins:
        status = getattr(plugin, 'compliance_status', {})
        if status.get('compliant', False):
            compliant_plugins.append({
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
                "response_model": status.get('response_model', 'Unknown')
            })
    
    return {
        "success": True,
        "rule": "ALL PLUGINS MUST DEFINE PYDANTIC RESPONSE MODELS",
        "summary": {
            "total_plugins": len(all_plugins),
            "compliant_count": len(compliant_plugins),
            "non_compliant_count": len(non_compliant),
            "compliance_percentage": round((len(compliant_plugins) / len(all_plugins) * 100) if all_plugins else 0, 2)
        },
        "compliant_plugins": compliant_plugins,
        "non_compliant_plugins": non_compliant,
        "fix_instructions": {
            "steps": [
                "Make your plugin class inherit from BasePlugin",
                "Define a Pydantic response model inheriting from BasePluginResponse", 
                "Implement the get_response_model() class method",
                "Ensure execute() returns data that validates against your model"
            ],
            "example_code": """
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from ...models.plugin import BasePlugin, BasePluginResponse

class YourPluginResponse(BasePluginResponse):
    result: str = Field(..., description="Your result field")
    count: int = Field(..., description="Some count")

class Plugin(BasePlugin):
    @classmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        return YourPluginResponse
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result": "some value",
            "count": 42
        }
            """
        }
    }


# ========== CHAIN MANAGEMENT ENDPOINTS ==========

@app.get("/chain-builder", response_class=HTMLResponse)
async def chain_builder(request: Request):
    """Visual chain builder interface"""
    return templates.TemplateResponse("chain_builder.html", {
        "request": request
    })

@app.get("/chains", response_class=HTMLResponse)
async def chains_list(request: Request):
    """List all chains interface"""
    chains = chain_manager.list_chains()
    return templates.TemplateResponse("chains.html", {
        "request": request,
        "chains": chains
    })

@app.post("/api/chains")
async def create_chain(chain_data: Dict[str, Any]):
    """Create a new plugin chain"""
    try:
        if "definition" in chain_data:
            # Save a complete chain definition
            chain = ChainDefinition(**chain_data["definition"])
            success = chain_manager.save_chain(chain)
            if success:
                return {"success": True, "chain_id": chain.id}
            else:
                raise HTTPException(status_code=500, detail="Failed to save chain")
        else:
            # Create a new empty chain
            chain = chain_manager.create_chain(
                name=chain_data.get("name", "Untitled Chain"),
                description=chain_data.get("description", ""),
                author=chain_data.get("author")
            )
            return {"success": True, "chain": chain.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/chains")
async def list_chains(tags: str = None, template_only: bool = False):
    """List all available chains"""
    tag_list = tags.split(",") if tags else None
    chains = chain_manager.list_chains(tags=tag_list, template_only=template_only)
    return {
        "success": True, 
        "chains": [chain.dict() for chain in chains]
    }

@app.get("/api/chains/search")
async def search_chains(q: str = "", tags: str = None):
    """Search chains by query and tags"""
    tag_list = tags.split(",") if tags else None
    results = chain_manager.search_chains(query=q, tags=tag_list)
    return {"success": True, "results": results}

@app.get("/api/chains/{chain_id}")
async def get_chain(chain_id: str):
    """Get a specific chain definition"""
    chain = chain_manager.load_chain(chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"success": True, "chain": chain.dict()}

@app.put("/api/chains/{chain_id}")
async def update_chain(chain_id: str, chain_data: Dict[str, Any]):
    """Update a chain definition"""
    try:
        chain = ChainDefinition(**chain_data)
        chain.id = chain_id  # Ensure ID matches URL
        success = chain_manager.save_chain(chain)
        if success:
            return {"success": True, "chain": chain.dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to update chain")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/chains/{chain_id}")
async def delete_chain(chain_id: str):
    """Delete a chain"""
    success = chain_manager.delete_chain(chain_id)
    if success:
        return {"success": True, "message": "Chain deleted"}
    else:
        raise HTTPException(status_code=404, detail="Chain not found")

@app.post("/api/chains/{chain_id}/duplicate")
async def duplicate_chain(chain_id: str, data: Dict[str, Any]):
    """Duplicate an existing chain"""
    new_name = data.get("name")
    duplicate = chain_manager.duplicate_chain(chain_id, new_name)
    if duplicate:
        return {"success": True, "chain": duplicate.dict()}
    else:
        raise HTTPException(status_code=404, detail="Chain not found")

@app.post("/api/chains/validate")
async def validate_chain(chain_data: Dict[str, Any]):
    """Validate a chain definition"""
    try:
        chain = ChainDefinition(**chain_data)
        validation = chain_manager.validate_chain(chain)
        return {"success": True, "validation": validation.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chains/{chain_id}/execute")
async def execute_chain(chain_id: str, input_data: Dict[str, Any]):
    """Execute a plugin chain"""
    try:
        result = await chain_manager.execute_chain(chain_id, input_data)
        return result.dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chains/{chain_id}/history")
async def get_execution_history(chain_id: str, limit: int = 50):
    """Get execution history for a chain"""
    history = chain_manager.get_execution_history(chain_id, limit)
    return {
        "success": True, 
        "history": [result.dict() for result in history]
    }

@app.get("/api/chains/{chain_id}/analytics")
async def get_chain_analytics(chain_id: str):
    """Get analytics for a specific chain"""
    analytics = chain_manager.get_chain_analytics(chain_id)
    if analytics:
        return {"success": True, "analytics": analytics.dict()}
    else:
        return {"success": True, "analytics": None}

@app.get("/api/system/analytics")
async def get_system_analytics():
    """Get system-wide analytics"""
    analytics = chain_manager.get_system_analytics()
    return {"success": True, "analytics": analytics}

@app.get("/api/plugins/{plugin_id}/schema")
async def get_plugin_schema(plugin_id: str):
    """Get plugin input/output schema for chain building"""
    schema = chain_manager.get_plugin_schema(plugin_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"success": True, "schema": schema}

@app.get("/api/chains/{chain_id}/connections/{source_node_id}")
async def get_compatible_connections(chain_id: str, source_node_id: str):
    """Get possible connections from a source node"""
    chain = chain_manager.load_chain(chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    compatible = chain_manager.get_compatible_connections(chain, source_node_id)
    return {"success": True, "compatible_connections": compatible}

# ========== TEMPLATE MANAGEMENT ==========

@app.get("/api/templates")
async def list_templates(category: str = None):
    """List all available templates"""
    templates = chain_manager.list_templates(category=category)
    return {
        "success": True, 
        "templates": [template.dict() for template in templates]
    }

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template"""
    template = chain_manager.load_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "template": template.dict()}

@app.post("/api/templates/{template_id}/create-chain")
async def create_chain_from_template(template_id: str, data: Dict[str, Any]):
    """Create a new chain from a template"""
    chain = chain_manager.create_chain_from_template(
        template_id, 
        data.get("name", "Untitled Chain"),
        data.get("author")
    )
    if chain:
        return {"success": True, "chain": chain.dict()}
    else:
        raise HTTPException(status_code=404, detail="Template not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 