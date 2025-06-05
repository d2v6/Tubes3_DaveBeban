import re
from typing import Dict, List

class TextPreprocessor:
    @staticmethod
    def clean_text_for_search(text: str) -> str:
        """
        Clean and normalize text for search operations by removing unwanted characters
        and normalizing whitespace while preserving essential punctuation.
        
        Args:
            text (str): Raw text to be cleaned
            
        Returns:
            str: Cleaned text ready for search operations
        """
        if not text:
            return ""
        
        try:
            # Normalize line breaks and whitespace - convert all types of line breaks to spaces
            text = re.sub(r'[\n\r\f\v\t]+', ' ', text)
            
            # Remove excessive spaces - collapse multiple spaces into single space
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep alphanumeric, spaces, and common punctuation
            # Preserves: letters, numbers, spaces, hyphens, periods, commas, semicolons, 
            # colons, parentheses, @ symbols, forward/back slashes
            text = re.sub(r'[^\w\s\-.,;:()@/\\]', ' ', text)
            
            # Final cleanup - remove leading/trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            print(f" Error cleaning text: {e}")
            return text.strip() if text else ""

    @staticmethod
    def prepare_for_matching(text: str, case_sensitive: bool = False) -> str:
        """
        Prepare text for pattern matching by cleaning and normalizing case.
        
        Args:
            text (str): Text to prepare for matching
            case_sensitive (bool): Whether to preserve case sensitivity
            
        Returns:
            str: Text prepared for pattern matching operations
        """
        if not text:
            return ""
        
        # Clean text first using the standard cleaning method
        cleaned = TextPreprocessor.clean_text_for_search(text)
        
        # Convert case based on matching requirements
        if not case_sensitive:
            cleaned = cleaned.lower()
        
        # Remove extra spaces that might affect pattern matching
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """
        Extract meaningful keywords from text by filtering out short words,
        punctuation, and duplicates while preserving important numbers like years.
        
        Args:
            text (str): Text to extract keywords from
            min_length (int): Minimum length for keywords (default: 2)
            
        Returns:
            List[str]: List of unique keywords extracted from text
        """
        if not text:
            return []
        
        # Clean text using standard cleaning method
        cleaned = TextPreprocessor.clean_text_for_search(text)
        
        # Split into individual words
        words = cleaned.split()
        
        # Filter keywords based on criteria
        keywords = []
        for word in words:
            # Remove punctuation at word boundaries
            clean_word = re.sub(r'^[^\w]+|[^\w]+$', '', word)
            
            # Keep words that meet length criteria
            # Special case: keep 4+ digit numbers (years, IDs, etc.)
            if (clean_word and 
                len(clean_word) >= min_length and
                not clean_word.isdigit() or len(clean_word) >= 4):  # Keep years (4+ digits)
                keywords.append(clean_word)
        
        # Remove duplicates while preserving original order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            # Use lowercase for duplicate detection but preserve original case
            if keyword.lower() not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword.lower())
        
        return unique_keywords

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Basic text normalization - lighter cleaning compared to clean_text_for_search.
        Primarily handles whitespace normalization.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text with cleaned whitespace
        """
        if not text:
            return ""
        
        # Basic normalization - convert tabs to spaces
        text = text.replace('\t', ' ')
        # Collapse multiple spaces into single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into individual sentences based on sentence-ending punctuation.
        Filters out very short segments that are likely not meaningful sentences.
        
        Args:
            text (str): Text to split into sentences
            
        Returns:
            List[str]: List of sentences with minimum meaningful length
        """
        if not text:
            return []
        
        # Split by sentence endings (periods, exclamation marks, question marks)
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Only keep sentences with meaningful length (>10 characters)
            if len(sentence) > 10:  # Minimum meaningful sentence length
                clean_sentences.append(sentence)
        
        return clean_sentences

    @staticmethod
    def get_text_stats(text: str) -> Dict[str, int]:
        """
        Calculate basic statistics about the text content.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, int]: Dictionary containing character count, word count, and line count
        """
        if not text:
            return {'characters': 0, 'words': 0, 'lines': 0}
        
        return {
            'characters': len(text),  # Total character count including spaces
            'words': len(text.split()),  # Word count based on whitespace splitting
            'lines': text.count('\n') + 1  # Line count based on newline characters
        }

    @staticmethod
    def prepare_cv_text(text: str) -> str:
        """
        Specialized text preparation for CV/resume content that preserves
        important formatting patterns like emails, phone numbers, and dates.
        
        Args:
            text (str): CV/resume text to prepare
            
        Returns:
            str: CV text with preserved important patterns and cleaned formatting
        """
        if not text:
            return ""
        
        # Step 1: Basic cleaning using standard method
        cleaned = TextPreprocessor.clean_text_for_search(text)
        
        # Step 2: Preserve important CV formatting patterns
        # Keep email patterns - add spaces around emails for better tokenization
        cleaned = re.sub(r'(\w+@\w+\.\w+)', r' \1 ', cleaned)
        
        # Keep phone patterns - preserve phone numbers with various formats
        cleaned = re.sub(r'(\+?\d[\d\-\s\(\)]{8,})', r' \1 ', cleaned)
        
        # Keep date patterns important for experience sections
        # Match MM/DD/YYYY or DD-MM-YYYY formats
        cleaned = re.sub(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})', r' \1 ', cleaned)
        # Match standalone years (important for graduation dates, work experience)
        cleaned = re.sub(r'(\d{4})', r' \1 ', cleaned)
        
        # Final cleanup - normalize whitespace after pattern preservation
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    @staticmethod
    def create_search_variant(text: str) -> Dict[str, str]:
        """
        Create both original and processed versions of text for flexible searching.
        Useful when you need to maintain original formatting while having a clean version.
        
        Args:
            text (str): Original text to create variants from
            
        Returns:
            Dict[str, str]: Dictionary with 'original' and 'processed' text versions
        """
        if not text:
            return {'original': '', 'processed': ''}
        
        # Process text using CV-specific preparation method
        processed = TextPreprocessor.prepare_cv_text(text)
        
        return {
            'original': text,      # Maintain original formatting
            'processed': processed  # Cleaned version for searching
        }
