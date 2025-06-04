import pypdf
from typing import Optional, Dict, List
import os
import logging
from .text_preprocessor import TextPreprocessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFParser:
    @staticmethod
    def parse_pdf(file_path: str) -> Optional[str]:
        """
        Enhanced PDF parsing with better error handling and validation
        """
        try:
            # Validate file path
            if not PDFParser._validate_pdf_file(file_path):
                return None
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    logger.warning(f"PDF is encrypted: {file_path}")
                    return None
                
                total_pages = len(pdf_reader.pages)
                if total_pages == 0:
                    logger.warning(f"PDF has no pages: {file_path}")
                    return None
                
                text_parts = []
                extracted_pages = 0
                
                for page_num in range(total_pages):
                    try:
                        page_obj = pdf_reader.pages[page_num]
                        page_text = page_obj.extract_text()
                        
                        if page_text.strip():  # Only add non-empty pages
                            text_parts.append(page_text)
                            extracted_pages += 1
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
                
                if extracted_pages == 0:
                    logger.error(f"No text could be extracted from PDF: {file_path}")
                    return None
                
                final_text = "\n".join(text_parts)
                logger.info(f"Successfully extracted text from {extracted_pages}/{total_pages} pages")
                
                return final_text.strip()
                
        except pypdf.errors.PdfReadError as e:
            logger.error(f"PDF read error for {file_path}: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing PDF {file_path}: {e}")
            return None

    @staticmethod
    def _validate_pdf_file(file_path: str) -> bool:
        """Validate PDF file before processing"""
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False
        
        if not os.path.isfile(file_path):
            logger.error(f"Path is not a file: {file_path}")
            return False
        
        if not file_path.lower().endswith('.pdf'):
            logger.error(f"File is not a PDF: {file_path}")
            return False
        
        # Check file size (max 50MB)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            logger.error(f"PDF file too large: {file_size} bytes (max {max_size})")
            return False
        
        return True

    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Alias for parse_pdf for backwards compatibility"""
        return PDFParser.parse_pdf(file_path)

    @staticmethod
    def parse_pdf_with_variants(file_path: str) -> Optional[Dict[str, str]]:
        """
        Enhanced PDF parsing with multiple text variants
        """
        try:
            logger.info(f"Processing PDF: {os.path.basename(file_path)}")
            
            # Extract raw text
            original_text = PDFParser.parse_pdf(file_path)
            
            if not original_text:
                logger.error(f"Failed to extract text from PDF: {file_path}")
                return None
            
            # Create search-optimized variants
            variants = TextPreprocessor.create_search_variants(original_text)
            
            # Add metadata
            variants['metadata'] = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'original_length': len(original_text),
                'processed_length': len(variants.get('flattened', '')),
                'extraction_successful': True
            }
            
            logger.info(f"Successfully created text variants for {os.path.basename(file_path)}")
            return variants
            
        except Exception as e:
            logger.error(f"Error creating PDF variants for {file_path}: {e}")
            return None

    @staticmethod
    def batch_parse_pdfs(file_paths: List[str]) -> Dict[str, Dict[str, str]]:
        """Parse multiple PDFs in batch with progress tracking"""
        results = {}
        total_files = len(file_paths)
        
        logger.info(f"Starting batch processing of {total_files} PDF files")
        
        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            logger.info(f"Processing {i}/{total_files}: {filename}")
            
            variants = PDFParser.parse_pdf_with_variants(file_path)
            if variants:
                results[filename] = variants
                logger.info(f"{i}/{total_files} completed: {filename}")
            else:
                logger.error(f" {i}/{total_files} failed: {filename}")
        
        success_rate = len(results) / total_files * 100
        logger.info(f"🎯 Batch processing complete: {len(results)}/{total_files} files ({success_rate:.1f}% success rate)")
        
        return results

    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict[str, any]:
        """Extract metadata from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                metadata = {
                    'page_count': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                    'file_size': os.path.getsize(file_path),
                    'filename': os.path.basename(file_path)
                }
                
                # Add PDF metadata if available
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}
