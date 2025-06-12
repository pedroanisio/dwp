# Dynamic Web Plugins

A modern web application featuring a dynamic plugin system built with FastAPI and Pydantic. Each plugin defines its own UI components and output specifications through a manifest-driven architecture.

## 🚀 Features

- **Dynamic Plugin Loading**: Plugins are discovered and loaded automatically at runtime
- **Manifest-Driven**: Plugin configuration through JSON manifests with Pydantic validation
- **Type Safety**: Full Pydantic validation for plugin inputs and outputs
- **Modern UI**: Bootstrap-based responsive interface with custom styling
- **RESTful API**: Complete API endpoints for programmatic access
- **Extensible**: Easy to add new plugins with custom logic and UI components

## 📁 Project Structure

```
├── requirements.txt        # Project dependencies
└── app/
    ├── main.py                 # FastAPI application entry point
    ├── models/
    │   ├── __init__.py
    │   ├── plugin.py          # Plugin manifest and interface models
    │   └── response.py        # Response models
    ├── core/
    │   ├── __init__.py
    │   ├── plugin_loader.py   # Plugin loading and management
    │   └── plugin_manager.py  # Plugin execution and UI rendering
    ├── plugins/
    │   ├── __init__.py
    │   └── text_stat/
    │       ├── __init__.py
    │       ├── manifest.json  # Plugin manifest
    │       └── plugin.py      # Plugin implementation
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── app.js
    └── templates/
        ├── base.html
        ├── index.html
        ├── plugin.html
        └── result.html
```

## 🛠️ Installation & Setup

1. **Clone or create the project structure** (if not already done)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   # From the project root directory
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the application**:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Plugin API: http://localhost:8000/api/plugins

## 📋 Sample Plugin: Text Statistics

The included `text_stat` plugin demonstrates the system capabilities:

### Input
- **Textarea** for free text input
- Validation for text length (1-100,000 characters)

### Output (textStat report)
- **Character counts** (with/without spaces)
- **Word analysis** (total, unique, average length)
- **Document structure** (lines, sentences)
- **Frequency analysis** (words and characters)
- **Advanced metrics** (vocabulary diversity)

### Example Usage
1. Navigate to http://localhost:8000
2. Click "Use Plugin" on the Text Statistics Analyzer
3. Enter text in the textarea
4. Click "Execute Plugin"
5. View comprehensive analysis results

## 🔌 Plugin Development

### 1. Plugin Manifest (`manifest.json`)

```json
{
  "id": "your_plugin_id",
  "name": "Your Plugin Name",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": "Your Name",
  "inputs": [
    {
      "name": "field_name",
      "label": "Field Label",
      "field_type": "textarea",
      "required": true,
      "placeholder": "Enter text...",
      "validation": {
        "min_length": 1,
        "max_length": 1000
      }
    },
    {
      "name": "input_file",
      "label": "Source File",
      "field_type": "file",
      "required": true,
      "validation": {
        "allowed_extensions": ["pdf", "docx"]
      },
      "help": "Upload the source document for processing."
    },
    {
      "name": "enable_feature",
      "label": "Enable Feature",
      "field_type": "checkbox",
      "required": false,
      "default_value": false,
      "help": "Check this to enable a special feature."
    }
  ],
  "output": {
    "name": "outputFormat",
    "description": "Output description",
    "schema": {
      "type": "object",
      "properties": {
        "result": {"type": "string"}
      }
    }
  },
  "tags": ["category1", "category2"],
  "dependencies": {
    "external": [
      {
        "name": "pandoc",
        "help": "Pandoc is required. On Debian/Ubuntu, install with 'sudo apt-get install pandoc'."
      }
    ],
    "python": [
      {
        "name": "numpy",
        "help": "numpy==1.21.0"
      }
    ]
  }
}
```

### 2. Plugin Implementation (`plugin.py`)

```python
class Plugin:
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin logic
        
        Args:
            data: Dictionary containing input field values
            
        Returns:
            Dictionary with results matching the output schema
        """
        # Your plugin logic here
        input_text = data.get('field_name', '')
        
        # Process the input
        result = process_data(input_text)
        
        return {
            "result": result,
            "metadata": {"processed_at": "2024-01-01T00:00:00Z"}
        }
```

### 3. Supported Input Field Types

- `text`: Single-line text input
- `textarea`: Multi-line text input
- `number`: Numeric input
- `select`: Dropdown selection
- `checkbox`: Boolean checkbox
- `file`: File upload

### 4. Adding Your Plugin

1. Create a new directory in `app/plugins/`
2. Add `__init__.py`, `manifest.json`, and `plugin.py`
3. Restart the application
4. Your plugin will be automatically discovered

## 🌐 API Endpoints

### Core Endpoints
- `GET /` - Web interface homepage
- `GET /plugin/{plugin_id}` - Plugin interaction page
- `POST /plugin/{plugin_id}/execute` - Execute plugin (web form)

### API Endpoints
- `GET /api/plugins` - List all available plugins
- `GET /api/plugin/{plugin_id}` - Get plugin information
- `POST /api/plugin/{plugin_id}/execute` - Execute plugin (JSON API)
- `POST /api/refresh-plugins` - Refresh plugin list

### Example API Usage

```bash
# List plugins
curl http://localhost:8000/api/plugins

# Execute text_stat plugin
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world! This is a test."}'
```

## 🏗️ Architecture

### Plugin Manager
- **Discovery**: Scans plugin directories for manifests
- **Loading**: Dynamically imports plugin modules
- **Validation**: Validates inputs against plugin schemas
- **Execution**: Runs plugin logic and captures results

### Validation System
- **Manifest Validation**: Pydantic models ensure valid plugin definitions
- **Input Validation**: Runtime validation of user inputs
- **Output Validation**: Ensures plugin outputs match declared schemas

### UI Generation
- **Dynamic Forms**: HTML forms generated from plugin manifests
- **Type-Aware Rendering**: Different input types render appropriately
- **Responsive Design**: Bootstrap-based responsive interface

## 🎨 Customization

### Adding New Field Types
1. Update `InputFieldType` enum in `models/plugin.py`
2. Add rendering logic in `templates/plugin.html`
3. Add validation logic in `core/plugin_manager.py`

### Custom Result Display
- Modify `templates/result.html` for specialized result rendering
- Add plugin-specific display logic using template conditionals

### Styling
- Customize `static/css/style.css` for visual modifications
- Extend `static/js/app.js` for additional functionality

## 🧪 Testing

### Test the Text Statistics Plugin
```bash
# Quick test with sample text
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet at least once!"
  }'
```

Expected results include character counts, word frequencies, and linguistic analysis.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your plugin or enhancement
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided as a demonstration of FastAPI + Pydantic plugin architecture patterns.

## 🔍 Troubleshooting

### Plugin Not Loading
- Check `manifest.json` syntax and required fields
- Ensure `plugin.py` has a `Plugin` class with `execute` method
- Verify plugin directory structure

### Validation Errors
- Check input field types match manifest definitions
- Ensure required fields are provided
- Validate JSON schema syntax

### Performance Issues
- Monitor plugin execution times in results
- Consider caching for frequently used plugins
- Optimize plugin logic for large inputs 