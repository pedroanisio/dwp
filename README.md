# Neural Plugin System with Chain Builder

This project is a modern, web-based application that features a dynamic plugin system with visual chain building capabilities, built with FastAPI and Pydantic. Each plugin can define its own user interface and I/O specifications through a simple, yet powerful, manifest-driven architecture. The system automatically discovers and loads plugins at runtime, and allows users to create complex workflows by chaining plugins together visually.

## 🚀 Key Features

- **Dynamic Plugin Loading**: Plugins are discovered and loaded on-the-fly without needing to restart the application.
- **Visual Chain Builder**: Create complex workflows by connecting plugins in a visual interface.
- **Manifest-Driven UI**: Each plugin's UI and inputs are defined in a `manifest.json` file, allowing for flexible and self-describing components.
- **Type-Safe Inputs**: Pydantic ensures all user inputs are validated against the types defined in the plugin's manifest.
- **🔒 Type-Safe Responses**: All plugins must define Pydantic models for their responses, ensuring consistent and validated outputs.
- **Plugin Compliance Checking**: Automatic validation that plugins follow the response model rule with detailed compliance reports.
- **Chain Management**: Save, load, duplicate, and manage plugin chains with execution history and analytics.
- **Template System**: Pre-built chain templates for common workflows.
- **Dependency Checking**: The system automatically checks for required external dependencies (e.g., command-line tools) and reports their status in the UI.
- **File-Based I/O**: Plugins can easily handle file uploads and generate downloadable file outputs.
- **Analytics Dashboard**: Track plugin usage, chain execution statistics, and system performance.
- **Modern Tech Stack**: Built with FastAPI, Pydantic, and a responsive web interface.

## 🔒 MANDATORY PLUGIN RESPONSE MODEL RULE

**ALL PLUGINS MUST DEFINE THE PYDANTIC MODEL OF ITS RESPONSE**

This rule ensures:
- ✅ Type safety and validation for all plugin responses
- ✅ Consistent API structure across all plugins  
- ✅ Self-documenting response formats
- ✅ Early detection of response structure issues
- ✅ Better developer experience and debugging
- ✅ Seamless chain compatibility and data flow validation

### Implementation Requirements

Every plugin must:

1. **Inherit from BasePlugin**
   ```python
   from ...models.plugin import BasePlugin, BasePluginResponse
   
   class Plugin(BasePlugin):
       # Your plugin implementation
   ```

2. **Define a Response Model**
   ```python
   class YourPluginResponse(BasePluginResponse):
       result: str = Field(..., description="Your result field")
       count: int = Field(..., description="Some count")
       data: Dict[str, Any] = Field(default={}, description="Additional data")
   ```

3. **Implement get_response_model() Method**
   ```python
   @classmethod
   def get_response_model(cls) -> Type[BasePluginResponse]:
       return YourPluginResponse
   ```

4. **Return Validated Data**
   ```python
   def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
       # Your plugin logic here
       return {
           "result": "processed successfully",
           "count": 42,
           "data": {"additional": "information"}
       }
   ```

### Response Model Benefits

- **Chain Compatibility**: Ensures outputs from one plugin can be safely used as inputs to another
- **Runtime Validation**: Catches data structure issues before they propagate through chains
- **API Documentation**: Auto-generates OpenAPI schemas for plugin responses
- **Type Safety**: Provides IDE support and reduces runtime errors
- **Debugging**: Clear error messages when response validation fails

## 📦 Available Plugins

The application includes 6 pre-built plugins demonstrating various capabilities:

1. **Text Statistics** (`text_stat`): Analyzes text and provides comprehensive statistics including word count, character count, frequency analysis, and linguistic metrics. ✅ **Compliant**

2. **Pandoc Converter** (`pandoc_converter`): Converts documents between formats using the Pandoc command-line tool (Markdown to DOCX, EPUB to HTML, etc.). ✅ **Compliant**

3. **JSON to XML Converter** (`json_to_xml`): Converts JSON data structures to XML format with customizable formatting options.

4. **XML to JSON Converter** (`xml_to_json`): Converts XML documents to JSON format with structure preservation.

5. **Document Viewer** (`doc_viewer`): Displays and analyzes document content with metadata extraction capabilities.

6. **Web Sentence Analyzer** (`web_sentence_analyzer`): Advanced sentence analysis with web-based natural language processing features.

**Plugin Compliance Status**: Use the compliance checker to verify which plugins follow the response model rule:
```bash
# Check compliance via API
curl http://localhost:8000/api/plugin-compliance
```

## 🔗 Chain Builder

The Chain Builder allows you to create complex workflows by connecting multiple plugins in sequence. Features include:

- **Visual Interface**: Drag-and-drop plugin connection at `/chain-builder`
- **Data Flow Validation**: Ensures output types match input requirements
- **Conditional Logic**: Support for branching and conditional execution
- **Template Library**: Pre-built chains for common use cases
- **Execution History**: Track and analyze chain performance
- **Real-time Monitoring**: Live execution status and progress tracking

### Creating Chains

1. **Via Web Interface**: Navigate to `/chain-builder` for the visual editor
2. **Via API**: Use the REST API to programmatically create chains
3. **From Templates**: Start with pre-built templates and customize

### Chain Templates

Access pre-built templates for common workflows:
- Document processing pipelines
- Text analysis workflows  
- Data transformation chains
- Multi-format conversion sequences

## ⚙️ Getting Started

### Prerequisites

- Python 3.9+
- Node.js and npm
- Optional: Pandoc (for document conversion plugins)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pedroanisio/dwp.git
   cd dynamic-web-plugins
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```bash
   npm install
   ```

4. Build the CSS:
   ```bash
   npm run build-css
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the application:
   - Main interface: http://localhost:8000
   - Chain Builder: http://localhost:8000/chain-builder
   - Plugin Development Guide: http://localhost:8000/how-to

## 🔌 Developing a New Plugin

Creating a new plugin requires following the **mandatory response model rule**. Here's the complete process:

### Required Steps

1. **Create Plugin Directory**
   ```bash
   mkdir app/plugins/your_plugin_name
   cd app/plugins/your_plugin_name
   ```

2. **Create manifest.json**
   ```json
   {
     "id": "your_plugin_name",
     "name": "Your Plugin Display Name",
     "version": "1.0.0",
     "description": "Description of what your plugin does",
     "author": "Your Name",
     "inputs": [
       {
         "name": "input_field",
         "label": "Input Label",
         "field_type": "text",
         "required": true,
         "placeholder": "Enter value..."
       }
     ],
     "output": {
       "name": "result",
       "description": "Plugin output description"
     },
     "dependencies": ["optional", "external", "tools"],
     "tags": ["category", "keywords"]
   }
   ```

3. **Create plugin.py with Response Model**
   ```python
   from typing import Dict, Any, Type
   from pydantic import Field
   from ...models.plugin import BasePlugin, BasePluginResponse

   class YourPluginResponse(BasePluginResponse):
       """Response model for your plugin"""
       result: str = Field(..., description="Processing result")
       metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

   class Plugin(BasePlugin):
       """Your plugin implementation"""
       
       @classmethod
       def get_response_model(cls) -> Type[BasePluginResponse]:
           return YourPluginResponse
       
       def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
           # Your plugin logic here
           input_value = data.get('input_field', '')
           
           # Process the input
           processed_result = f"Processed: {input_value}"
           
           return {
               "result": processed_result,
               "metadata": {
                   "input_length": len(input_value),
                   "processing_time": "0.1s"
               }
           }
   ```

4. **Test Your Plugin**
   ```bash
   # Check compliance
   curl http://localhost:8000/api/plugin-compliance
   
   # Test execution
   curl -X POST http://localhost:8000/api/plugin/your_plugin_name/execute \
     -H "Content-Type: application/json" \
     -d '{"input_field": "test data"}'
   ```

### Plugin Development Best Practices

- **Response Validation**: Always validate your response data matches the model
- **Error Handling**: Use appropriate exception types for different error scenarios
- **Documentation**: Include clear descriptions in your response model fields
- **Dependencies**: List all external dependencies in the manifest
- **Testing**: Test both successful execution and error cases

## 📁 Project Structure

```
├── requirements.txt                    # Python dependencies
├── package.json                       # Node.js dependencies and scripts
├── docker-compose.yml                 # Docker configuration
├── Dockerfile                         # Container definition
├── tailwind.config.js                 # Tailwind CSS configuration
├── postcss.config.js                  # PostCSS configuration
└── app/
    ├── main.py                         # FastAPI application entry point
    ├── models/
    │   ├── __init__.py
    │   ├── plugin.py                  # Plugin models + BasePlugin + BasePluginResponse
    │   ├── response.py                # API response models
    │   └── chain.py                   # Chain definition models
    ├── core/
    │   ├── __init__.py
    │   ├── plugin_loader.py           # Plugin discovery and loading
    │   ├── plugin_manager.py          # Plugin execution + compliance checking
    │   ├── chain_manager.py           # Chain execution and management
    │   ├── chain_executor.py          # Chain execution engine
    │   └── chain_storage.py           # Chain persistence layer
    ├── plugins/
    │   ├── __init__.py
    │   ├── text_stat/                 # Text statistics plugin
    │   ├── pandoc_converter/          # Document converter plugin
    │   ├── json_to_xml/               # JSON to XML converter
    │   ├── xml_to_json/               # XML to JSON converter
    │   ├── doc_viewer/                # Document viewer plugin
    │   └── web_sentence_analyzer/     # Sentence analysis plugin
    ├── static/
    │   ├── css/
    │   │   ├── dist/                  # Compiled CSS
    │   │   └── src/                   # Source CSS files
    │   ├── js/
    │   │   └── app.js                 # Client-side JavaScript
    │   └── favicon.ico
    ├── templates/
    │   ├── base.html                  # Base template
    │   ├── index.html                 # Homepage
    │   ├── plugin.html                # Plugin execution page
    │   ├── result.html                # Results display
    │   ├── chain_builder.html         # Chain builder interface
    │   ├── chains.html                # Chain management
    │   └── how-to.html                # Development guide
    └── data/                          # Data storage directory
        ├── chains/                    # Saved chains
        └── templates/                 # Chain templates
```

## 🌐 API Endpoints

### Core Plugin Endpoints

- `GET /` - Web interface homepage
- `GET /plugin/{plugin_id}` - Plugin interaction page
- `GET /how-to` - Plugin development guide
- `POST /plugin/{plugin_id}/execute` - Execute plugin (web form)

### Plugin API Endpoints

- `GET /api/plugins` - List all available plugins
- `GET /api/plugin/{plugin_id}` - Get plugin information
- `GET /api/plugin/{plugin_id}/schema` - Get plugin input/output schema
- `POST /api/plugin/{plugin_id}/execute` - Execute plugin (JSON API)
- `POST /api/refresh-plugins` - Refresh plugin list
- `GET /api/plugin-compliance` - Check plugin compliance status

### Chain Management Endpoints

- `GET /chain-builder` - Visual chain builder interface
- `GET /chains` - Chain management interface
- `GET /api/chains` - List all chains
- `POST /api/chains` - Create new chain
- `GET /api/chains/search` - Search chains
- `GET /api/chains/{chain_id}` - Get specific chain
- `PUT /api/chains/{chain_id}` - Update chain
- `DELETE /api/chains/{chain_id}` - Delete chain
- `POST /api/chains/{chain_id}/duplicate` - Duplicate chain
- `POST /api/chains/validate` - Validate chain definition
- `POST /api/chains/{chain_id}/execute` - Execute chain
- `GET /api/chains/{chain_id}/history` - Get execution history
- `GET /api/chains/{chain_id}/analytics` - Get chain analytics
- `GET /api/chains/{chain_id}/connections/{source_node_id}` - Get compatible connections

### Template Management Endpoints

- `GET /api/templates` - List available templates
- `GET /api/templates/{template_id}` - Get specific template
- `POST /api/templates/{template_id}/create-chain` - Create chain from template

### System Endpoints

- `GET /api/system/analytics` - System-wide analytics

### Example API Usage

```bash
# List all plugins
curl http://localhost:8000/api/plugins

# Check plugin compliance
curl http://localhost:8000/api/plugin-compliance

# Execute text statistics plugin
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world! This is a test."}'

# List all chains
curl http://localhost:8000/api/chains

# Create a new chain
curl -X POST http://localhost:8000/api/chains \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workflow", "description": "Custom processing workflow"}'

# Execute a chain
curl -X POST http://localhost:8000/api/chains/chain_id/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": "your data here"}'
```

## 🏗️ Architecture

### Plugin System Architecture

- **Discovery**: Scans plugin directories for manifests automatically
- **Loading**: Dynamically imports plugin modules at runtime
- **Compliance Checking**: Validates plugins follow response model requirements
- **Validation**: Validates inputs against plugin schemas using Pydantic
- **Response Validation**: Ensures plugin outputs match declared response models
- **Execution**: Runs plugin logic with error handling and result capture

### Chain Builder Architecture

- **Visual Editor**: Web-based drag-and-drop interface for chain creation
- **Execution Engine**: Processes chains with data flow validation
- **Storage Layer**: Persists chains and execution history
- **Analytics Engine**: Tracks performance metrics and usage statistics
- **Template System**: Manages reusable chain templates

### Validation System

- **Manifest Validation**: Pydantic models ensure valid plugin definitions
- **Input Validation**: Runtime validation of user inputs against schemas
- **Plugin Compliance**: Ensures plugins inherit from BasePlugin and define response models
- **Output Validation**: Validates plugin outputs against declared Pydantic response models
- **Chain Validation**: Ensures data compatibility between connected plugins

### UI Generation

- **Dynamic Forms**: HTML forms generated from plugin manifests
- **Type-Aware Rendering**: Different input types render with appropriate controls
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: Live feedback during plugin and chain execution

## 🔍 Plugin Compliance Checking

### API Compliance Check

Get detailed compliance reports for all plugins:

```bash
curl http://localhost:8000/api/plugin-compliance
```

Response includes:
- Total plugin count and compliance percentage
- List of compliant plugins with response models
- List of non-compliant plugins with specific issues
- Migration instructions and example code

### Compliance Requirements

All plugins must:

1. **Inherit from BasePlugin**
2. **Define a response model inheriting from BasePluginResponse**
3. **Implement get_response_model() class method**
4. **Return data that validates against the response model**
5. **Handle errors gracefully with appropriate response structure**

### Migration Guide for Existing Plugins

If you have non-compliant plugins, follow these steps:

1. **Add Response Model**
   ```python
   class YourPluginResponse(BasePluginResponse):
       # Define your response fields here
       pass
   ```

2. **Update Plugin Class**
   ```python
   class Plugin(BasePlugin):  # Ensure BasePlugin inheritance
       @classmethod
       def get_response_model(cls) -> Type[BasePluginResponse]:
           return YourPluginResponse
   ```

3. **Validate Execute Method**
   ```python
   def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
       # Ensure return data matches your response model
       return {"field1": "value1", "field2": "value2"}
   ```

## 📊 Analytics and Monitoring

### Chain Analytics

Track chain performance with detailed metrics:
- Execution frequency and success rates
- Average execution time per chain
- Error patterns and failure analysis
- Resource usage statistics

### System Analytics

Monitor overall system health:
- Plugin usage statistics
- Popular chain templates
- System performance metrics
- User activity patterns

### Access Analytics

- **Chain-specific**: `GET /api/chains/{chain_id}/analytics`
- **System-wide**: `GET /api/system/analytics`
- **Execution History**: `GET /api/chains/{chain_id}/history`

## 🎨 Customization

### Adding New Field Types

1. Update `InputFieldType` enum in `models/plugin.py`
2. Add rendering logic in `templates/plugin.html`
3. Add validation logic in `core/plugin_manager.py`
4. Update chain builder to handle new field types

### Custom Result Display

- Modify `templates/result.html` for specialized result rendering
- Add plugin-specific display logic using template conditionals
- Create custom CSS classes for enhanced visualization

### Chain Builder Customization

- Extend `static/js/app.js` for custom node types
- Add custom connection validation logic
- Implement specialized chain execution patterns

### Styling and Theming

- Customize `static/css/src/main.css` for visual modifications
- Modify Tailwind configuration in `tailwind.config.js`
- Add custom components and layouts

## 🧪 Testing

### Test Plugin Compliance

```bash
# Check if all plugins are compliant
curl http://localhost:8000/api/plugin-compliance
```

### Test Individual Plugins

```bash
# Test the Text Statistics Plugin
curl -X POST http://localhost:8000/api/plugin/text_stat/execute \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet!"
  }'

# Test the Pandoc Converter (requires file upload)
curl -X POST http://localhost:8000/api/plugin/pandoc_converter/execute \
  -F "input_file=@document.md" \
  -F "output_format=html"
```

### Test Chain Execution

```bash
# Validate a chain definition
curl -X POST http://localhost:8000/api/chains/validate \
  -H "Content-Type: application/json" \
  -d '{"chain_definition": "your_chain_json_here"}'

# Execute a chain
curl -X POST http://localhost:8000/api/chains/your_chain_id/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": "test input"}'
```

## 🐳 Docker Deployment

The project includes Docker configuration for easy deployment:

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build manually
docker build -t neural-plugin-system .
docker run -p 8000:8000 neural-plugin-system
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. **Ensure any new plugins follow the response model rule**
4. **Run compliance checker**: `curl http://localhost:8000/api/plugin-compliance`
5. Test thoroughly (plugins, chains, and UI)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Submit a pull request

### Contribution Guidelines

- All plugins must be compliant with response model requirements
- Include comprehensive tests for new features
- Update documentation for any API changes
- Follow existing code style and patterns
- Add chain templates for common use cases

## 📄 License

This project is provided as a demonstration of FastAPI + Pydantic plugin architecture patterns with advanced chain building capabilities.

## 🔍 Troubleshooting

### Plugin Issues

**Plugin Not Loading:**
- Check `manifest.json` syntax and required fields
- Ensure plugin inherits from `BasePlugin`
- Verify plugin implements `get_response_model()` method
- Ensure `plugin.py` has a `Plugin` class with `execute` method
- Check plugin directory structure matches requirements

**Plugin Compliance Issues:**
- Run compliance check: `curl http://localhost:8000/api/plugin-compliance`
- Ensure response model inherits from `BasePluginResponse`
- Verify `execute()` returns data matching the response model schema
- Check that all required fields are properly defined

**Validation Errors:**
- Check input field types match manifest definitions
- Ensure required fields are provided in requests
- Validate JSON schema syntax in manifests
- Verify plugin response validation against defined models

### Chain Builder Issues

**Chain Not Executing:**
- Validate chain definition using `/api/chains/validate`
- Check data type compatibility between connected plugins
- Verify all required inputs are provided
- Check execution history for error details

**Connection Issues:**
- Use `/api/chains/{chain_id}/connections/{source_node_id}` to check compatibility
- Ensure output types match input requirements
- Verify plugin response models are properly defined

**Performance Issues:**
- Monitor execution times in chain analytics
- Check system analytics for resource usage
- Optimize plugin logic for large inputs
- Consider caching for frequently used chains

### System Issues

**Response Model Validation Failures:**
- Verify plugin response data matches the defined Pydantic model
- Check field types and required fields in response model
- Use compliance checker to identify specific validation issues
- Ensure all plugins return valid response structures

**Database/Storage Issues:**
- Check file permissions in `app/data/` directories
- Verify chain storage integrity
- Clear temporary files if disk space is low
- Check execution history logs for patterns

**Dependencies:**
- Ensure all external tools (like Pandoc) are installed
- Check Python package versions match requirements.txt
- Verify Node.js dependencies are properly installed
- Test external tool availability in plugin manifests

For additional support, check the execution logs and use the built-in analytics to identify patterns in errors or performance issues.
