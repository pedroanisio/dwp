import time
from typing import Dict, Any, Optional, List
from ..models.plugin import PluginManifest, PluginInput, PluginOutput
from ..models.response import PluginExecutionResponse
from .plugin_loader import PluginLoader


class PluginManager:
    def __init__(self):
        self.loader = PluginLoader()
        self.plugins: Dict[str, PluginManifest] = {}
        self.refresh_plugins()
    
    def refresh_plugins(self):
        """Refresh the list of available plugins"""
        self.plugins = self.loader.discover_plugins()
    
    def get_all_plugins(self) -> List[PluginManifest]:
        """Get all available plugins"""
        return list(self.plugins.values())
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """Get a specific plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def execute_plugin(self, plugin_input: PluginInput) -> PluginExecutionResponse:
        """Execute a plugin with the given input"""
        start_time = time.time()
        
        try:
            # Check if plugin exists
            if plugin_input.plugin_id not in self.plugins:
                return PluginExecutionResponse(
                    success=False,
                    plugin_id=plugin_input.plugin_id,
                    error=f"Plugin '{plugin_input.plugin_id}' not found"
                )
            
            # Load plugin class
            plugin_class = self.loader.get_plugin_class(plugin_input.plugin_id)
            if not plugin_class:
                return PluginExecutionResponse(
                    success=False,
                    plugin_id=plugin_input.plugin_id,
                    error=f"Could not load plugin class for '{plugin_input.plugin_id}'"
                )
            
            # Validate input against plugin manifest
            manifest = self.plugins[plugin_input.plugin_id]
            validation_error = self._validate_input(plugin_input.data, manifest)
            if validation_error:
                return PluginExecutionResponse(
                    success=False,
                    plugin_id=plugin_input.plugin_id,
                    error=validation_error
                )
            
            # Execute plugin
            plugin_instance = plugin_class()
            result = plugin_instance.execute(plugin_input.data)
            
            execution_time = time.time() - start_time
            
            return PluginExecutionResponse(
                success=True,
                plugin_id=plugin_input.plugin_id,
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return PluginExecutionResponse(
                success=False,
                plugin_id=plugin_input.plugin_id,
                error=str(e),
                execution_time=execution_time
            )
    
    def _validate_input(self, data: Dict[str, Any], manifest: PluginManifest) -> Optional[str]:
        """Validate input data against plugin manifest"""
        for input_field in manifest.inputs:
            field_name = input_field.name
            
            # Check required fields
            if input_field.required and field_name not in data:
                return f"Required field '{field_name}' is missing"
            
            # Skip validation for optional missing fields
            if field_name not in data:
                continue
            
            field_value = data[field_name]
            
            # Type validation based on field type
            if input_field.field_type == "number":
                try:
                    float(field_value)
                except (ValueError, TypeError):
                    return f"Field '{field_name}' must be a number"
            
            elif input_field.field_type == "checkbox":
                if not isinstance(field_value, bool):
                    return f"Field '{field_name}' must be a boolean"
            
            elif input_field.field_type == "select":
                if input_field.options and field_value not in input_field.options:
                    return f"Field '{field_name}' must be one of: {', '.join(input_field.options)}"
        
        return None 