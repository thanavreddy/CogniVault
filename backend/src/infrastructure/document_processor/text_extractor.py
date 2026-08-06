import os
from pypdf import PdfReader
from docx import Document as DocxDocument
from src.domain.entities.document import DocumentType

class TextExtractor:
    def extract(self, file_path: str, document_type: DocumentType) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if document_type == DocumentType.PDF:
            return self.extract_pdf(file_path)
        elif document_type == DocumentType.DOCX:
            return self.extract_docx(file_path)
        elif document_type in (DocumentType.TXT, DocumentType.MARKDOWN):
            return self.extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

    def extract_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text.strip()

    def extract_docx(self, file_path: str) -> str:
        doc = DocxDocument(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs]).strip()

    def extract_txt(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
