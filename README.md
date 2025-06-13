
# Dynamic Web-Based Plugin System

This project is a modern, web-based application that features a dynamic plugin system built with FastAPI and Pydantic. Each plugin can define its own user interface and I/O specifications through a simple, yet powerful, manifest-driven architecture. The system automatically discovers and loads plugins at runtime, making it highly extensible and easy to maintain.

## 🚀 Key Features

- **Dynamic Plugin Loading**: Plugins are discovered and loaded on-the-fly without needing to restart the application.
- **Manifest-Driven UI**: Each plugin's UI and inputs are defined in a `manifest.json` file, allowing for flexible and self-describing components.
- **Type-Safe Inputs**: Pydantic ensures all user inputs are validated against the types defined in the plugin's manifest.
- **Dependency Checking**: The system automatically checks for required external dependencies (e.g., command-line tools) and reports their status in the UI.
- **File-Based I/O**: Plugins can easily handle file uploads and generate downloadable file outputs.
- **Modern Tech Stack**: Built with FastAPI, Pydantic, and a Bootstrap-based responsive UI.

## 📦 Included Plugins

The application comes with three pre-built plugins to demonstrate its capabilities:

1.  **Text Statistics**: A powerful tool for analyzing text. It takes a string as input and returns a detailed report including word count, character count, frequency analysis, and more.
2.  **Pandoc Converter**: A versatile document converter that leverages the `pandoc` command-line tool. It can convert files between a wide variety of formats (e.g., Markdown to DOCX, EPUB to HTML).
3.  **Pandoc JSON to XML**: A specialized plugin that converts Pandoc's JSON AST (Abstract Syntax Tree) into a minimal XML format.

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

The application will be available at http://localhost:8000.

## 🔌 Developing a New Plugin

Creating a new plugin is straightforward. For detailed instructions and examples, please see the **"How to Build Plugins"** page within the web application, available at http://localhost:8000/how-to.

The basic steps are:
1.  Create a new directory in `app/plugins/`.
2.  Add a `manifest.json` file to define your plugin's UI and dependencies.
3.  Write your plugin's logic in a `plugin.py` file.

The application will automatically detect and load your new plugin.

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