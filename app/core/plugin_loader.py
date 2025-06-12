import os
import json
import importlib.util
from typing import Dict, Any, Optional
from pathlib import Path
from ..models.plugin import PluginManifest


class PluginLoader:
    def __init__(self, plugins_dir: str = "app/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        
    def discover_plugins(self) -> Dict[str, PluginManifest]:
        """Discover all plugins in the plugins directory"""
        plugins = {}
        
        if not self.plugins_dir.exists():
            return plugins
            
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('__'):
                manifest_path = plugin_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        plugin_manifest = self._load_manifest(manifest_path)
                        plugins[plugin_manifest.id] = plugin_manifest
                    except Exception as e:
                        print(f"Error loading plugin {plugin_dir.name}: {e}")
                        
        return plugins
    
    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        """Load and validate plugin manifest"""
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        return PluginManifest(**manifest_data)
    
    def load_plugin_module(self, plugin_id: str) -> Optional[Any]:
        """Load the plugin module dynamically"""
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id]["module"]
            
        plugin_dir = self.plugins_dir / plugin_id
        plugin_file = plugin_dir / "plugin.py"
        
        if not plugin_file.exists():
            return None
            
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_id}.plugin", 
                plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.loaded_plugins[plugin_id] = {
                "module": module,
                "path": plugin_file
            }
            
            return module
        except Exception as e:
            print(f"Error loading plugin module {plugin_id}: {e}")
            return None
    
    def get_plugin_class(self, plugin_id: str):
        """Get the plugin class from the loaded module"""
        module = self.load_plugin_module(plugin_id)
        if module and hasattr(module, 'Plugin'):
            return module.Plugin
        return None 