import xml.etree.ElementTree as ET
from typing import List, Union, Optional, Literal
from pydantic import BaseModel, Field

# --- Define the building blocks (nodes) for content ---

class BaseNode(BaseModel):
    """A base model for all content nodes."""
    pass

class TextNode(BaseNode):
    """Represents plain text content."""
    type: Literal["text"] = "text"
    content: str

class EmphasisNode(BaseNode):
    """Represents emphasized text, from an <E> tag."""
    type: Literal["emphasis"] = "emphasis"
    content: str

class StructuralNode(BaseNode):
    """Represents structural elements like lines or placeholders."""
    type: Literal["structural"] = "structural"
    element_type: str  # e.g., "HorizontalRule", "Span", "Image", "Link", "Table"

class RawHtmlNode(BaseNode):
    """Represents a block of raw HTML content."""
    type: Literal["raw_html"] = "raw_html"
    content: str
    
# A Union type for any inline content that can appear within a paragraph or heading.
InlineContent = Union[TextNode, EmphasisNode, StructuralNode, RawHtmlNode]

# --- Define the main block-level components of the document ---

class BaseBlock(BaseModel):
    """A base model for all block-level content."""
    pass

class HeadingNode(BaseBlock):
    """Represents a heading, from an <H> tag."""
    type: Literal["heading"] = "heading"
    level: int
    content: List[InlineContent]

class ParagraphNode(BaseBlock):
    """Represents a paragraph, from a <P> tag."""
    type: Literal["paragraph"] = "paragraph"
    # The label from an <S> tag, e.g., "Title", "Author"
    semantic_label: Optional[str] = None
    content: List[InlineContent]

class DivNode(BaseBlock):
    """Represents a division or container, from a <DIV> tag."""
    type: Literal["div"] = "div"
    content: List['ContentBlock'] # Using ForwardRef as a string

class QuoteNode(BaseBlock):
    """Represents a blockquote, from a <Q> tag."""
    type: Literal["quote"] = "quote"
    content: List['ContentBlock']

# A Union type for any block-level content.
ContentBlock = Union[HeadingNode, ParagraphNode, DivNode, QuoteNode, RawHtmlNode, StructuralNode]

# Update forward references for nested models
DivNode.model_rebuild()
QuoteNode.model_rebuild()

# --- Define the top-level document model ---

class DocumentMetadata(BaseModel):
    """Model for the document's metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    release_date: Optional[str] = None
    language: Optional[str] = None
    credits: Optional[str] = None

class PrincipiaDocument(BaseModel):
    """The root model for the entire parsed document."""
    metadata: DocumentMetadata
    body: List[ContentBlock] 