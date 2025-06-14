# Dynamic Web-Based Plugin System

This project is a modern, web-based application that features a dynamic plugin system built with FastAPI and Pydantic. Each plugin can define its own user interface and I/O specifications through a simple, yet powerful, manifest-driven architecture. The system automatically discovers and loads plugins at runtime, making it highly extensible and easy to maintain.

## 🚀 Key Features

- **Dynamic Plugin Loading**: Plugins are discovered and loaded on-the-fly without needing to restart the application.
- **Manifest-Driven UI**: Each plugin's UI and inputs are defined in a `manifest.json` file, allowing for flexible and self-describing components.
- **Type-Safe Inputs**: Pydantic ensures all user inputs are validated against the types defined in the plugin's manifest.
- **🔒 Type-Safe Responses**: **NEW** - All plugins must define Pydantic models for their responses, ensuring consistent and validated outputs.
- **Plugin Compliance Checking**: Automatic validation that plugins follow the response model rule with detailed compliance reports.
- **Dependency Checking**: The system automatically checks for required external dependencies (e.g., command-line tools) and reports their status in the UI.
- **File-Based I/O**: Plugins can easily handle file uploads and generate downloadable file outputs.
- **Modern Tech Stack**: Built with FastAPI, Pydantic, and a Bootstrap-based responsive UI.

## 🔒 MANDATORY PLUGIN RULE

**ALL PLUGINS MUST DEFINE THE PYDANTIC MODEL OF ITS RESPONSE**

This rule ensures:

- ✅ Type safety and validation for all plugin responses
- ✅ Consistent API structure across all plugins  
- ✅ Self-documenting response formats
- ✅ Early detection of response structure issues
- ✅ Better developer experience and debugging

See [PLUGIN_RESPONSE_MODEL_RULE.md](PLUGIN_RESPONSE_MODEL_RULE.md) for complete implementation details.

## 📦 Included Plugins

The application comes with several pre-built plugins to demonstrate its capabilities:

1. **Text Statistics**: A powerful tool for analyzing text. It takes a string as input and returns a detailed report including word count, character count, frequency analysis, and more. ✅ **Compliant with response model rule**
2. **Pandoc Converter**: A versatile document converter that leverages the `pandoc` command-line tool. It can convert files between a wide variety of formats (e.g., Markdown to DOCX, EPUB to HTML).
3. **Pandoc JSON to XML**: A specialized plugin that converts Pandoc's JSON AST (Abstract Syntax Tree) into a minimal XML format.

**Note**: Some existing plugins may need to be updated to comply with the response model rule. Use the compliance checker to identify which plugins need updates.

## 🛠️ Getting Started

Follow these steps to get the application up and running:

### 1. Installation

First, clone the repository and install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Install External Dependencies

Some plugins, like the Pandoc Converter, rely on external command-line tools. You'll need to install `pandoc` on your system. On Debian/Ubuntu, you can do so with:

```bash
sudo apt-get update && sudo apt-get install pandoc
```

### 3. Running the Application

Once everything is installed, you can run the web server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at <http://localhost:8000>.

### 4. Check Plugin Compliance

Check that all plugins follow the response model rule:

```bash
python check_plugin_compliance.py
```

## 🔌 Developing a New Plugin

Creating a new plugin requires following the **mandatory response model rule**. Here's the updated basic process:

### Required Steps

1. Create a new directory in `app/plugins/`
2. Add a `manifest.json` file to define your plugin's UI and dependencies
3. **NEW**: Define a Pydantic response model inheriting from `BasePluginResponse`
4. Write your plugin class inheriting from `BasePlugin`
5. Implement the required `get_response_model()` method
6. Ensure your `execute()` method returns data matching your response model

### Quick Example

```python
from typing import Dict, Any, Type
from pydantic import Field
from ...models.plugin import BasePlugin, BasePluginResponse

class MyPluginResponse(BasePluginResponse):
    result: str = Field(..., description="Processing result")
    count: int = Field(..., description="Number of items processed")

class Plugin(BasePlugin):
    @classmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        return MyPluginResponse
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result": "processed data",
            "count": 42
        }
```

For detailed instructions and examples, see:

- **"How to Build Plugins"** page at <http://localhost:8000/how-to>
- [PLUGIN_RESPONSE_MODEL_RULE.md](PLUGIN_RESPONSE_MODEL_RULE.md) for complete compliance guide

## 📁 Project Structure

```
├── requirements.txt                    # Project dependencies
├── check_plugin_compliance.py         # Plugin compliance checker script
├── PLUGIN_RESPONSE_MODEL_RULE.md      # Response model rule documentation
└── app/
    ├── main.py                         # FastAPI application entry point
    ├── models/
    │   ├── __init__.py
    │   ├── plugin.py                  # Plugin models + BasePlugin + BasePluginResponse
    │   └── response.py                # API response models
    ├── core/
    │   ├── __init__.py
    │   ├── plugin_loader.py           # Plugin discovery and loading
    │   └── plugin_manager.py          # Plugin execution + compliance checking
    ├── plugins/
    │   ├── __init__.py
    │   └── text_stat/                 # Example compliant plugin
    │       ├── __init__.py
    │       ├── manifest.json          # Plugin manifest
    │       └── plugin.py              # Plugin implementation
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
- **NEW**: `GET /api/plugin-compliance` - Check plugin compliance with response model rule

### Example API Usage

```bash
# List plugins
curl http://localhost:8000/api/plugins

# Check plugin compliance
curl http://localhost:8000/api/plugin-compliance

# Execute text_stat plugin
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world! This is a test."}'
```

## 🏗️ Architecture

### Plugin Manager

- **Discovery**: Scans plugin directories for manifests
- **Loading**: Dynamically imports plugin modules
- **Compliance Checking**: **NEW** - Validates plugins follow response model rule
- **Validation**: Validates inputs against plugin schemas
- **Response Validation**: **NEW** - Validates plugin outputs against defined response models
- **Execution**: Runs plugin logic and captures results

### Validation System

- **Manifest Validation**: Pydantic models ensure valid plugin definitions
- **Input Validation**: Runtime validation of user inputs
- **Plugin Compliance**: **NEW** - Ensures plugins inherit from BasePlugin and define response models
- **Output Validation**: **NEW** - Ensures plugin outputs match declared Pydantic response models

### UI Generation

- **Dynamic Forms**: HTML forms generated from plugin manifests
- **Type-Aware Rendering**: Different input types render appropriately
- **Responsive Design**: Bootstrap-based responsive interface

## 🔍 Plugin Compliance Checking

### Command Line Checker

```bash
# Check all plugins for compliance
python check_plugin_compliance.py

# Exit codes: 0 = all compliant, 1 = some non-compliant
```

### API Compliance Check

```bash
# Get detailed compliance report
curl http://localhost:8000/api/plugin-compliance
```

### Compliance Requirements

All plugins must:

1. Inherit from `BasePlugin`
2. Define a response model inheriting from `BasePluginResponse`
3. Implement `get_response_model()` class method
4. Return data that validates against the response model

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

### Test Plugin Compliance

```bash
# Check if all plugins are compliant
python check_plugin_compliance.py
```

### Test the Text Statistics Plugin

```bash
# Quick test with sample text
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet at least once!"
  }'
```

Expected results include character counts, word frequencies, and linguistic analysis - all validated against the `TextStatResponse` model.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. **NEW**: Ensure any new plugins follow the response model rule
4. **NEW**: Run compliance checker: `python check_plugin_compliance.py`
5. Test thoroughly
6. Submit a pull request

## 📄 License

This project is provided as a demonstration of FastAPI + Pydantic plugin architecture patterns.

## 🔍 Troubleshooting

### Plugin Not Loading

- Check `manifest.json` syntax and required fields
- **NEW**: Ensure plugin inherits from `BasePlugin`
- **NEW**: Verify plugin implements `get_response_model()` method
- Ensure `plugin.py` has a `Plugin` class with `execute` method
- Verify plugin directory structure

### Plugin Compliance Issues

- **NEW**: Run `python check_plugin_compliance.py` for detailed error reports
- **NEW**: Check that response model inherits from `BasePluginResponse`
- **NEW**: Ensure `execute()` returns data matching the response model schema
- **NEW**: See [PLUGIN_RESPONSE_MODEL_RULE.md](PLUGIN_RESPONSE_MODEL_RULE.md) for migration guide

### Validation Errors

- Check input field types match manifest definitions
- Ensure required fields are provided
- Validate JSON schema syntax
- **NEW**: Check plugin response validation errors in execution results

### Performance Issues

- Monitor plugin execution times in results
- Consider caching for frequently used plugins
- Optimize plugin logic for large inputs

### Response Model Validation Failures

- **NEW**: Verify plugin response data matches the defined Pydantic model
- **NEW**: Check field types and required fields in response model
- **NEW**: Use the compliance checker to identify specific validation issues
