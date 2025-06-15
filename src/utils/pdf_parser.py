import pdfplumber
import os
from typing import Optional

class PDFParser:
    """Simple PDF parser to extract text content"""
    
    @staticmethod
    def parse_pdf(file_path: str) -> Optional[str]:
        """Parse PDF file and extract text content"""
        try:
            if not os.path.exists(file_path):
                return None
            
            text_content = ""
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
            return text_content.strip() if text_content.strip() else None
                
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return None