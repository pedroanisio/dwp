import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

# Use the pandoc library for parsing
import pandoc
from pandoc.types import (
    Pandoc, Meta, Block, Inline, Str, Space, Code, Emph, Strong, SoftBreak,
    LineBreak, Para, Plain, Header, CodeBlock, BulletList, BlockQuote, Div,
    RawBlock, RawInline
)

def _emit_inlines(parent: ET.Element, lst: List[Inline]):
    for inl in lst:
        if isinstance(inl, Str):
            parent.text = (parent.text or "") + inl[0]
        elif isinstance(inl, Space):
            parent.text = (parent.text or "") + " "
        elif isinstance(inl, Code):
            attr, text = inl
            ET.SubElement(parent, "C").text = text
        elif isinstance(inl, Emph):
            e = ET.SubElement(parent, "E")
            _emit_inlines(e, inl[0])
        elif isinstance(inl, Strong):
            s = ET.SubElement(parent, "S")
            _emit_inlines(s, inl[0])
        elif isinstance(inl, (SoftBreak, LineBreak)):
            ET.SubElement(parent, "BR")
        elif isinstance(inl, RawInline):
            format_obj, text = inl
            ET.SubElement(parent, "Raw", format=format_obj[0]).text = text
        else:
            ET.SubElement(parent, "U", t=type(inl).__name__)

def _emit(root: ET.Element, node: Block):
    if isinstance(node, (Para, Plain)):
        elem = ET.SubElement(root, "P")
        _emit_inlines(elem, node[0])
    elif isinstance(node, Header):
        level, attr, inlines = node
        elem = ET.SubElement(root, "H", l=str(level))
        _emit_inlines(elem, inlines)
    elif isinstance(node, CodeBlock):
        attr, text = node
        lang = attr[1][0] if attr[1] else ""
        ET.SubElement(root, "C", l=lang).text = text
    elif isinstance(node, BulletList):
        l = ET.SubElement(root, "L")
        for item in node[0]:
            i = ET.SubElement(l, "I")
            for blk in item:
                _emit(i, blk)
    elif isinstance(node, BlockQuote):
        q = ET.SubElement(root, "Q")
        for blk in node[0]:
            _emit(q, blk)
    elif isinstance(node, Div):
        attr, blocks = node
        div_elem = ET.SubElement(root, "DIV")
        for blk in blocks:
            _emit(div_elem, blk)
    elif isinstance(node, RawBlock):
        format_obj, text = node
        ET.SubElement(root, "RawBlock", format=format_obj[0]).text = text
    else:
        ET.SubElement(root, "U", t=type(node).__name__)

class Plugin:
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        file_info = data.get("input_file")
        if not file_info:
            raise ValueError("Missing JSON file input")

        try:
            json_string = file_info["content"].decode("utf-8")
            api_version = []
            
            try:
                raw_doc = json.loads(json_string)
                if isinstance(raw_doc, dict):
                    api_version = raw_doc.get("pandoc-api-version", [])
                doc = pandoc.read(json_string, format='json')
            except Exception:
                # Fallback for plain text or invalid format
                root = ET.Element("D")
                ET.SubElement(root, "B").text = json_string
                ET.indent(root)
                xml_output = ET.tostring(root, encoding="unicode")
                return {"xml_output": xml_output}

            meta, blocks = doc
            root = ET.Element("D", v=".".join(map(str, api_version)))
            
            ET.SubElement(root, "M")  # meta placeholder
            xml_blocks = ET.SubElement(root, "B")
            
            for blk in blocks:
                _emit(xml_blocks, blk)
            
            ET.indent(root)
            xml_output = ET.tostring(root, encoding="unicode")
            
            return {"xml_output": xml_output}

        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during XML conversion: {e}") 