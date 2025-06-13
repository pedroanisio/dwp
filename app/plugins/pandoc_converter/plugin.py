from pathlib import Path
import subprocess
import tempfile
from typing import Dict, Any, Type
import os
from pydantic import BaseModel, Field
from ...models.plugin import BasePlugin, BasePluginResponse


class PandocConverterResponse(BasePluginResponse):
    """Pydantic model for pandoc converter plugin response"""
    file_path: str = Field(..., description="Path to the converted file")
    file_name: str = Field(..., description="Name of the converted file")


class Plugin(BasePlugin):
    """Pandoc File Converter Plugin - Converts files between markup formats using Pandoc"""
    
    @classmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        """Return the Pydantic model for this plugin's response"""
        return PandocConverterResponse
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        input_file_info = data.get("input_file")
        output_format = data.get("output_format")
        self_contained = data.get("self_contained", False)

        if not input_file_info or not output_format:
            raise ValueError("Missing input file or output format")

        
        temp_dir = tempfile.mkdtemp()
        
        try:
            
            input_filename = input_file_info["filename"]
            input_file_content = input_file_info["content"]

            
            input_path = Path(temp_dir) / input_filename
            with open(input_path, "wb") as f:
                f.write(input_file_content)

            
            output_filename = f"{input_path.stem}.{output_format}"
            output_path = Path(temp_dir) / output_filename
            
            
            command = ["pandoc", str(input_path), "-o", str(output_path)]
            if self_contained:
                command.append("--self-contained")
            
            subprocess.run(
                command,
                check=True
            )

            
            return {
                "file_path": str(output_path),
                "file_name": output_filename
            }
        except subprocess.CalledProcessError as e:
            
            error_message = f"Pandoc conversion failed: {e}"
            if e.stderr:
                error_message += f"\nPandoc error: {e.stderr.decode()}"
            raise RuntimeError(error_message)
        except Exception as e:
            
            raise RuntimeError(f"An unexpected error occurred: {e}") 