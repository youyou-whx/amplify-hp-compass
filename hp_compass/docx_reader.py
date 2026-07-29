from __future__ import annotations

import re
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_docx_text(path: Path) -> str:
    """Read visible paragraph text from a docx file without external packages."""
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for para in root.iter(f"{W_NS}p"):
        chunks: list[str] = []
        for node in para.iter():
            if node.tag == f"{W_NS}t" and node.text:
                chunks.append(node.text)
            elif node.tag == f"{W_NS}tab":
                chunks.append("\t")
        text = unescape("".join(chunks)).strip()
        if text:
            paragraphs.append(text)

    return normalize_text("\n".join(paragraphs))


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_inputs(input_path: str | Path) -> list[tuple[Path, str]]:
    path = Path(input_path)
    if path.is_file() and path.suffix.lower() == ".docx":
        return [(path, read_docx_text(path))]
    if path.is_dir():
        # Skip hidden files, Word temp/owner files (~$...), and non-docx
        files = sorted(
            f for f in path.glob("*.docx")
            if not f.name.startswith("~$") and not f.name.startswith(".")
        )
        results: list[tuple[Path, str]] = []
        for file in files:
            try:
                text = read_docx_text(file)
                results.append((file, text))
            except Exception as exc:
                print(f"[WARN] Skipping {file.name}: {exc}")
        return results
    raise FileNotFoundError(f"Input path must be a .docx file or folder: {path}")

