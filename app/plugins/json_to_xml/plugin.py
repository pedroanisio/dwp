import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from pydantic import ValidationError
from .models import Pandoc, Block, Inline

def _emit_inlines(parent: ET.Element, lst: List[Inline]):
    for inl in lst:
        if inl.t == "Str":
            parent.text = (parent.text or "") + inl.c
        elif inl.t == "Space":
            parent.text = (parent.text or "") + " "
        elif inl.t == "Code":
            ET.SubElement(parent, "C").text = inl.c[1]
        elif inl.t == "Emph":
            e = ET.SubElement(parent, "E")
            _emit_inlines(e, inl.c)
        elif inl.t == "Strong":
            s = ET.SubElement(parent, "S")
            _emit_inlines(s, inl.c)
        elif inl.t in ("SoftBreak", "LineBreak"):
            ET.SubElement(parent, "BR")
        else:
            ET.SubElement(parent, "U", t=inl.t)

def _emit(root: ET.Element, node: Block):
    if node.t in ("Para", "Plain"):
        elem = ET.SubElement(root, "P")
        _emit_inlines(elem, node.c)
    elif node.t == "Header":
        lvl, inl, _ = node.c
        elem = ET.SubElement(root, "H", l=str(lvl))
        _emit_inlines(elem, inl)
    elif node.t == "CodeBlock":
        (_, code) = node.c
        lang = node.c[0][1][0] if node.c[0][1] else ""
        ET.SubElement(root, "C", l=lang).text = code
    elif node.t == "BulletList":
        l = ET.SubElement(root, "L")
        for item in node.c:
            i = ET.SubElement(l, "I")
            for blk in item:
                _emit(i, blk)
    elif node.t == "BlockQuote":
        q = ET.SubElement(root, "Q")
        for blk in node.c:
            _emit(q, blk)
    elif node.t in ("SoftBreak", "LineBreak"):
        ET.SubElement(root, "BR")
    else:
        ET.SubElement(root, "U", t=node.t).text = json.dumps(node.c)

class Plugin:
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        file_info = data.get("input_file")
        if not file_info:
            raise ValueError("Missing JSON file input")

        try:
            json_string = file_info["content"].decode("utf-8")
            
            try:
                doc = Pandoc.model_validate_json(json_string)
            except (ValidationError, json.JSONDecodeError):
                 # Fallback for plain text or invalid format
                root = ET.Element("D")
                ET.SubElement(root, "B").text = json_string
                ET.indent(root)
                xml_output = ET.tostring(root, encoding="unicode")
                return {"xml_output": xml_output}

            root = ET.Element("D", v=".".join(map(str, doc.pandoc_api_version)))
            
            ET.SubElement(root, "M")  # meta placeholder
            blocks = ET.SubElement(root, "B")
            
            for blk in doc.blocks:
                _emit(blocks, blk)
            
            ET.indent(root)
            xml_output = ET.tostring(root, encoding="unicode")
            
            return {"xml_output": xml_output}

        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during XML conversion: {e}") 