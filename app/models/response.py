from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from .plugin import PluginManifest


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class PluginListResponse(BaseModel):
    success: bool
    count: int = 0
    plugins: List[PluginManifest] = []

    def __init__(self, success: bool, plugins: List[PluginManifest], **kwargs):
        super().__init__(success=success, count=len(plugins), plugins=plugins, **kwargs)


class PluginExecutionResponse(BaseModel):
    success: bool
    plugin_id: str
    data: Optional[Dict[str, Any]] = None
    file_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None 