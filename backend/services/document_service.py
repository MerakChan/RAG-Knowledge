import os

class DocumentService:
    @staticmethod
    def parse_document(file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.txt':
            return DocumentService.parse_txt(file_path)
        elif file_extension == '.pdf':
            return DocumentService.parse_pdf(file_path)
        elif file_extension == '.docx' or file_extension == '.doc':
            return DocumentService.parse_docx(file_path)
        elif file_extension == '.rtf':
            return DocumentService.parse_rtf(file_path)
        elif file_extension == '.md':
            return DocumentService.parse_md(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    @staticmethod
    def parse_txt(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_pdf(file_path):
        try:
            import pdfplumber
            text = ''
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ''
            return text
        except ImportError:
            return "PDF parsing requires pdfplumber library"
    
    @staticmethod
    def parse_docx(file_path):
        try:
            from docx import Document
            doc = Document(file_path)
            text = ''
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
            return text
        except ImportError:
            return "DOCX parsing requires python-docx library"
    
    @staticmethod
    def parse_rtf(file_path):
        try:
            from striprtf.striprtf import rtf_to_text
            with open(file_path, 'r', encoding='utf-8') as f:
                rtf_content = f.read()
            return rtf_to_text(rtf_content)
        except ImportError:
            return "RTF parsing requires striprtf library"
    
    @staticmethod
    def parse_md(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
