from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_pdf_text(
    file_path: str,
) -> str:

    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def extract_docx_text(
    file_path: str,
) -> str:

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_text(
    file_path: str,
    file_type: str,
) -> str:

    if file_type == "pdf":

        return extract_pdf_text(
            file_path
        )

    if file_type == "docx":

        return extract_docx_text(
            file_path
        )

    raise ValueError(
        "Unsupported file type"
    )