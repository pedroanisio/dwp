from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


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