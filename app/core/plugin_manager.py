import time
import shutil
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
        for plugin in self.plugins.values():
            self._check_dependencies(plugin)
    
    def _check_dependencies(self, plugin: PluginManifest):
        """Check plugin dependencies and update its status"""
        plugin.dependency_status = {"all_met": True, "details": []}

        if not plugin.dependencies:
            return

        if plugin.dependencies.external:
            for dep in plugin.dependencies.external:
                is_met = shutil.which(dep.name) is not None
                if not is_met:
                    plugin.dependency_status["all_met"] = False
                plugin.dependency_status["details"].append({"name": dep.name, "met": is_met})
    
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

            # Check if dependencies are met before execution
            if hasattr(manifest, 'dependency_status') and not manifest.dependency_status["all_met"]:
                return PluginExecutionResponse(
                    success=False,
                    plugin_id=plugin_input.plugin_id,
                    error="Cannot execute plugin due to unmet dependencies."
                )

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
            
            # Check if the result contains file data
            if "file_path" in result and "file_name" in result:
                return PluginExecutionResponse(
                    success=True,
                    plugin_id=plugin_input.plugin_id,
                    file_data=result,
                    execution_time=execution_time
                )

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
            
            elif input_field.field_type == "file" and input_field.validation:
                allowed_extensions = input_field.validation.get("allowed_extensions")
                if allowed_extensions and isinstance(field_value, dict):
                    filename = field_value.get("filename", "")
                    file_ext = filename.split(".")[-1].lower()
                    if file_ext not in allowed_extensions:
                        return f"Invalid file type for '{field_name}'. Allowed types are: {', '.join(allowed_extensions)}"

        return None 