from typing import Dict, Any, List, Optional, Union, Type
from pydantic import BaseModel, Field
from enum import Enum
from abc import ABC, abstractmethod


class InputFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    SELECT = "select"
    CHECKBOX = "checkbox"
    FILE = "file"


class InputField(BaseModel):
    name: str = Field(..., description="Field name used as identifier")
    label: str = Field(..., description="Human-readable label for the field")
    field_type: InputFieldType = Field(..., description="Type of input field")
    required: bool = Field(default=True, description="Whether this field is required")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    options: Optional[List[str]] = Field(default=None, description="Options for select fields")
    default_value: Optional[Union[str, int, bool]] = Field(default=None, description="Default value")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    help_text: Optional[str] = Field(default=None, description="Help text for the field", alias="help")


class OutputFormat(BaseModel):
    name: str = Field(..., description="Output format name")
    description: str = Field(..., description="Description of the output")
    schema_definition: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for output validation", alias="schema")


class Dependency(BaseModel):
    name: str
    help_text: Optional[str] = Field(default=None, alias="help")


class PluginDependencies(BaseModel):
    external: Optional[List[Dependency]] = None
    python: Optional[List[Dependency]] = None


class PluginManifest(BaseModel):
    id: str = Field(..., description="Unique plugin identifier")
    name: str = Field(..., description="Human-readable plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: Optional[str] = Field(default=None, description="Plugin author")
    inputs: List[InputField] = Field(..., description="Input field definitions")
    output: OutputFormat = Field(..., description="Output format specification")
    tags: Optional[List[str]] = Field(default=None, description="Plugin tags for categorization")
    dependencies: Optional[PluginDependencies] = Field(default=None, description="Plugin dependencies")

    class Config:
        extra = "allow"


class PluginInput(BaseModel):
    plugin_id: str
    data: Dict[str, Any]


class PluginOutput(BaseModel):
    plugin_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BasePluginResponse(BaseModel):
    """Base class for all plugin response models"""
    pass


class BasePlugin(ABC):
    """
    Base class for all plugins. 
    
    RULE: All plugins MUST define a Pydantic model for their response by implementing
    the get_response_model() method and ensure their execute() method returns data
    that validates against this model.
    """
    
    @abstractmethod
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin with the given input data.
        
        Args:
            data: Input data dictionary. For plugins that handle files, the 'input_file'
                  key will contain a dictionary with either a 'temp_path' (for files
                  on disk) or 'content' (for in-memory file data). Plugins MUST
                  handle both cases gracefully.
            
        Returns:
            Dictionary that MUST validate against the model returned by get_response_model()
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        """
        Return the Pydantic model class that defines the structure of this plugin's response.
        
        This is REQUIRED for all plugins. The response from execute() must validate
        against this model.
        
        Returns:
            Pydantic model class inheriting from BasePluginResponse
        """
        pass
    
    def validate_response(self, response_data: Dict[str, Any]) -> BasePluginResponse:
        """
        Validate the response data against the plugin's response model.
        
        Args:
            response_data: The response data to validate
            
        Returns:
            Validated response model instance
            
        Raises:
            ValidationError: If the response doesn't match the model
        """
        response_model = self.get_response_model()
        return response_model(**response_data) 