from pathlib import Path

from loguru import logger


def parse_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def parse_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def parse_text(file_path: str) -> str:
    with open(file_path, encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_file(file_path: str, file_type: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_type.lower().lstrip(".")
    logger.debug(f"Parsing file: {path.name} (type={ext})")

    try:
        if ext == "pdf":
            return parse_pdf(file_path)
        elif ext == "docx":
            return parse_docx(file_path)
        elif ext in ("txt", "md"):
            return parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Failed to parse {path.name}: {e}")
        raise
