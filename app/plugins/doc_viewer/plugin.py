import json
from typing import Dict, Any
from .models import PrincipiaDocument

class Plugin:
    """
    Document Viewer Plugin - Renders a structured JSON document.
    """
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads the JSON file and returns the data along with a
        path to the custom template for rendering.
        """
        file_info = data.get("input_file")
        if not file_info:
            raise ValueError("Missing JSON file input")

        try:
            json_content = file_info["content"].decode("utf-8")
            document_data = json.loads(json_content)
            document = PrincipiaDocument(**document_data)
            
            return {
                "custom_template": "doc_viewer_view.html",
                "document": document.model_dump()
            }
        except Exception as e:
            raise ValueError(f"Error processing document: {e}") 