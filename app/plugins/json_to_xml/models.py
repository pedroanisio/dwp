from __future__ import annotations
from typing import Any, List, Dict, Tuple, Union, Literal
from pydantic import BaseModel, Field

# Basic Types
Attr = Tuple[str, List[str], List[Tuple[str, str]]]
Target = Tuple[str, str]
QuoteType = Union[Literal["SingleQuote"], Literal["DoubleQuote"]]
MathType = Union[Literal["DisplayMath"], Literal["InlineMath"]]

# Base classes for recursive models
class BaseElement(BaseModel):
    t: str
    c: Any

# Inline Elements
class Str(BaseModel):
    t: Literal["Str"]
    c: str

class Emph(BaseModel):
    t: Literal["Emph"]
    c: List[Inline]

class Underline(BaseModel):
    t: Literal["Underline"]
    c: List[Inline]

class Strong(BaseModel):
    t: Literal["Strong"]
    c: List[Inline]

class Strikeout(BaseModel):
    t: Literal["Strikeout"]
    c: List[Inline]

class Superscript(BaseModel):
    t: Literal["Superscript"]
    c: List[Inline]

class Subscript(BaseModel):
    t: Literal["Subscript"]
    c: List[Inline]

class SmallCaps(BaseModel):
    t: Literal["SmallCaps"]
    c: List[Inline]

class Quoted(BaseModel):
    t: Literal["Quoted"]
    c: Tuple[QuoteType, List[Inline]]

class Cite(BaseModel):
    t: Literal["Cite"]
    c: Tuple[List[Citation], List[Inline]]

class Code(BaseModel):
    t: Literal["Code"]
    c: Tuple[Attr, str]

class Space(BaseModel):
    t: Literal["Space"]
    c: None = None

class SoftBreak(BaseModel):
    t: Literal["SoftBreak"]
    c: None = None

class LineBreak(BaseModel):
    t: Literal["LineBreak"]
    c: None = None

class Math(BaseModel):
    t: Literal["Math"]
    c: Tuple[MathType, str]

class RawInline(BaseModel):
    t: Literal["RawInline"]
    c: Tuple[str, str]

class Link(BaseModel):
    t: Literal["Link"]
    c: Tuple[Attr, List[Inline], Target]

class Image(BaseModel):
    t: Literal["Image"]
    c: Tuple[Attr, List[Inline], Target]

class Note(BaseModel):
    t: Literal["Note"]
    c: List[Block]

class Span(BaseModel):
    t: Literal["Span"]
    c: Tuple[Attr, List[Inline]]

Inline = Union[
    Str, Emph, Underline, Strong, Strikeout, Superscript, Subscript, SmallCaps,
    Quoted, Cite, Code, Space, SoftBreak, LineBreak, Math, RawInline, Link,
    Image, Note, Span
]

# Block Elements
class Plain(BaseModel):
    t: Literal["Plain"]
    c: List[Inline]

class Para(BaseModel):
    t: Literal["Para"]
    c: List[Inline]

class LineBlock(BaseModel):
    t: Literal["LineBlock"]
    c: List[List[Inline]]

class CodeBlock(BaseModel):
    t: Literal["CodeBlock"]
    c: Tuple[Attr, str]

class RawBlock(BaseModel):
    t: Literal["RawBlock"]
    c: Tuple[str, str]

class BlockQuote(BaseModel):
    t: Literal["BlockQuote"]
    c: List[Block]

class OrderedList(BaseModel):
    t: Literal["OrderedList"]
    c: Tuple[ListAttributes, List[List[Block]]]

class BulletList(BaseModel):
    t: Literal["BulletList"]
    c: List[List[Block]]

class DefinitionList(BaseModel):
    t: Literal["DefinitionList"]
    c: List[Tuple[List[Inline], List[List[Block]]]]

class Header(BaseModel):
    t: Literal["Header"]
    c: Tuple[int, Attr, List[Inline]]

class HorizontalRule(BaseModel):
    t: Literal["HorizontalRule"]
    c: None = None

class Table(BaseModel):
    t: Literal["Table"]
    c: Any  # Complex, define if needed

class Div(BaseModel):
    t: Literal["Div"]
    c: Tuple[Attr, List[Block]]

class Null(BaseModel):
    t: Literal["Null"]
    c: None = None

Block = Union[
    Plain, Para, LineBlock, CodeBlock, RawBlock, BlockQuote, OrderedList,
    BulletList, DefinitionList, Header, HorizontalRule, Table, Div, Null
]

# Meta Value
class MetaValue(BaseModel):
    t: str
    c: Any

# Citation
class Citation(BaseModel):
    citationId: str
    citationPrefix: List[Inline]
    citationSuffix: List[Inline]
    citationMode: Any
    citationNoteNum: int
    citationHash: int

# List Attributes
ListAttributes = Tuple[int, Any, Any]

# Pandoc Document
class Pandoc(BaseModel):
    pandoc_api_version: List[int] = Field(..., alias="pandoc-api-version")
    meta: Dict[str, MetaValue]
    blocks: List[Block]

# Update forward references
Emph.model_rebuild()
Underline.model_rebuild()
Strong.model_rebuild()
Strikeout.model_rebuild()
Superscript.model_rebuild()
Subscript.model_rebuild()
SmallCaps.model_rebuild()
Quoted.model_rebuild()
Cite.model_rebuild()
Link.model_rebuild()
Image.model_rebuild()
Note.model_rebuild()
Span.model_rebuild()
Plain.model_rebuild()
Para.model_rebuild()
LineBlock.model_rebuild()
BlockQuote.model_rebuild()
OrderedList.model_rebuild()
BulletList.model_rebuild()
DefinitionList.model_rebuild()
Header.model_rebuild()
Div.model_rebuild() 