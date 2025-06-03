import pypdf
from typing import Optional

class PDFParser:
    @staticmethod
    def parse_pdf(file_path: str) -> Optional[str]:
        """Parse PDF file and extract text content"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page_obj = pdf_reader.pages[page_num]
                    text += page_obj.extract_text()
                    text += "\n"
                
                return text.strip()
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None