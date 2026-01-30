from __future__ import annotations

import argparse
import datetime as _dt
import html
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def _xml_escape(text: str) -> str:
    return html.escape(text, quote=False)


def _iso_now() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    code: bool = False


@dataclass(frozen=True)
class Block:
    kind: str  # heading|para|bullet|code|blank
    text: str = ""
    level: int = 0  # heading level (1..)


_RE_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RE_BULLET = re.compile(r"^\s*-\s+(.*)$")


def parse_markdown(md: str) -> list[Block]:
    lines = md.splitlines()
    blocks: list[Block] = []

    in_code = False
    code_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            if in_code:
                blocks.append(Block(kind="code", text="\n".join(code_lines)))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            blocks.append(Block(kind="blank"))
            continue

        m_h = _RE_HEADING.match(line)
        if m_h:
            level = len(m_h.group(1))
            text = m_h.group(2).strip()
            blocks.append(Block(kind="heading", text=text, level=level))
            continue

        m_b = _RE_BULLET.match(line)
        if m_b:
            blocks.append(Block(kind="bullet", text=m_b.group(1).strip()))
            continue

        blocks.append(Block(kind="para", text=line.strip()))

    if in_code and code_lines:
        blocks.append(Block(kind="code", text="\n".join(code_lines)))

    # Collapse consecutive blanks
    collapsed: list[Block] = []
    for b in blocks:
        if b.kind == "blank" and collapsed and collapsed[-1].kind == "blank":
            continue
        collapsed.append(b)
    return collapsed


def _parse_inline_runs(text: str) -> list[Run]:
    """
    Very small subset:
    - **bold**
    - `code`
    """
    runs: list[Run] = []
    i = 0
    while i < len(text):
        if text.startswith("**", i):
            j = text.find("**", i + 2)
            if j != -1:
                runs.append(Run(text=text[i + 2 : j], bold=True))
                i = j + 2
                continue
        if text.startswith("`", i):
            j = text.find("`", i + 1)
            if j != -1:
                runs.append(Run(text=text[i + 1 : j], code=True))
                i = j + 1
                continue
        # plain text until next marker
        nexts = [p for p in [text.find("**", i), text.find("`", i)] if p != -1]
        j = min(nexts) if nexts else len(text)
        runs.append(Run(text=text[i:j]))
        i = j
    # Merge adjacent plain runs
    merged: list[Run] = []
    for r in runs:
        if not r.text:
            continue
        if merged and not any([merged[-1].bold, merged[-1].code, r.bold, r.code]):
            merged[-1] = Run(text=merged[-1].text + r.text)
        else:
            merged.append(r)
    return merged


def _w_p(runs: list[Run], style: str | None = None) -> str:
    ppr = ""
    if style:
        ppr = f"<w:pPr><w:pStyle w:val=\"{_xml_escape(style)}\"/></w:pPr>"

    r_xml = []
    for run in runs:
        rpr_bits = []
        if run.bold:
            rpr_bits.append("<w:b/>")
        if run.code:
            rpr_bits.append("<w:rFonts w:ascii=\"Consolas\" w:hAnsi=\"Consolas\"/>")
        rpr = f"<w:rPr>{''.join(rpr_bits)}</w:rPr>" if rpr_bits else ""
        text = _xml_escape(run.text)
        # preserve leading/trailing spaces
        space_attr = " xml:space=\"preserve\"" if run.text[:1].isspace() or run.text[-1:].isspace() else ""
        r_xml.append(f"<w:r>{rpr}<w:t{space_attr}>{text}</w:t></w:r>")

    return f"<w:p>{ppr}{''.join(r_xml)}</w:p>"


def _w_code_block(text: str) -> str:
    # Represent each line as its own paragraph with code font.
    paras = []
    for line in text.splitlines() or [""]:
        paras.append(_w_p([Run(text=line, code=True)], style="Code"))
    return "".join(paras)


def build_document_xml(blocks: list[Block], title: str) -> str:
    body_parts: list[str] = []

    # Title as Heading1
    body_parts.append(_w_p([Run(text=title, bold=True)], style="Title"))
    body_parts.append(_w_p([Run(text="")]))

    for b in blocks:
        if b.kind == "blank":
            body_parts.append(_w_p([Run(text="")]))
            continue
        if b.kind == "heading":
            style = f"Heading{min(max(b.level, 1), 6)}"
            body_parts.append(_w_p(_parse_inline_runs(b.text), style=style))
            continue
        if b.kind == "bullet":
            body_parts.append(_w_p(_parse_inline_runs("• " + b.text)))
            continue
        if b.kind == "para":
            body_parts.append(_w_p(_parse_inline_runs(b.text)))
            continue
        if b.kind == "code":
            body_parts.append(_w_code_block(b.text))
            continue

    # Minimal section properties
    sect = (
        "<w:sectPr>"
        "<w:pgSz w:w=\"12240\" w:h=\"15840\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "</w:sectPr>"
    )
    body = "".join(body_parts) + sect

    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>{body}</w:body></w:document>'
    )


def styles_xml() -> str:
    # Minimal styles to ensure headings render as headings in Word.
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="20"/></w:rPr>
  </w:style>
  {''.join([f'''
  <w:style w:type="paragraph" w:styleId="Heading{i}">
    <w:name w:val="heading {i}"/>
    <w:basedOn w:val="Normal"/>
    <w:uiPriority w:val="{9-i}"/>
    <w:qFormat/>
    <w:rPr><w:b/><w:sz w:val="{max(24, 34 - i*2)}"/></w:rPr>
  </w:style>''' for i in range(1,7)])}
</w:styles>
"""


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def rels_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def doc_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""


def core_props_xml(title: str) -> str:
    now = _iso_now()
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="{CP_NS}" xmlns:dc="{DC_NS}" xmlns:dcterms="{DCTERMS_NS}" xmlns:xsi="{XSI_NS}">
  <dc:title>{_xml_escape(title)}</dc:title>
  <dc:creator>WebCAF</dc:creator>
  <cp:lastModifiedBy>WebCAF</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>
"""


def app_props_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>WebCAF</Application>
</Properties>
"""


def write_docx(markdown_path: Path, output_path: Path, title: str) -> None:
    md = markdown_path.read_text(encoding="utf-8")
    blocks = parse_markdown(md)
    document = build_document_xml(blocks, title=title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml())
        z.writestr("_rels/.rels", rels_xml())
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/_rels/document.xml.rels", doc_rels_xml())
        z.writestr("docProps/core.xml", core_props_xml(title))
        z.writestr("docProps/app.xml", app_props_xml())


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a subset of Markdown to a minimal .docx")
    ap.add_argument("--in", dest="input", required=True, help="Input markdown path")
    ap.add_argument("--out", dest="output", required=True, help="Output docx path")
    ap.add_argument("--title", default="Document", help="Document title")
    args = ap.parse_args()

    markdown_path = Path(args.input)
    output_path = Path(args.output)
    write_docx(markdown_path, output_path, title=args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
