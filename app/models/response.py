from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .plugin import PluginManifest


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class PluginListResponse(BaseModel):
    success: bool
    plugins: List[PluginManifest]


class PluginExecutionResponse(BaseModel):
    success: bool
    plugin_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None 