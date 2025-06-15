"""
String Matching Algorithms Collection

This module provides a unified interface to various string matching algorithms
including KMP, Boyer-Moore, Aho-Corasick, and Levenshtein distance.
"""

from .kmp_search import KMPSearch
from .boyer_moore_search import BoyerMooreSearch
from .aho_corasick_search import AhoCorasickSearch
from .levenshtein_distance import LevenshteinDistance
from typing import List, Dict

class StringMatcher:
    """
    Unified interface for all string matching algorithms
    
    Provides backward compatibility and easy access to all algorithms
    """
    
    # KMP Methods
    @staticmethod
    def kmp_search(text: str, pattern: str) -> List[int]:
        """Search using KMP algorithm"""
        return KMPSearch.search(text, pattern)
    
    # Boyer-Moore Methods
    @staticmethod
    def boyer_moore_search(text: str, pattern: str) -> List[int]:
        """Search using Boyer-Moore algorithm"""
        return BoyerMooreSearch.search(text, pattern)
    
    # Aho-Corasick Methods
    @staticmethod
    def aho_corasick_search(text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """Search using Aho-Corasick algorithm"""
        return AhoCorasickSearch.search(text, patterns)
    
    @staticmethod
    def aho_corasick_with_stats(text: str, patterns: List[str]) -> Dict:
        """Search using Aho-Corasick with statistics"""
        return AhoCorasickSearch.search_with_stats(text, patterns)
    
    # Levenshtein Methods
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        return LevenshteinDistance.calculate_distance(s1, s2)
    
    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        """Calculate similarity percentage"""
        return LevenshteinDistance.calculate_similarity(s1, s2)
    
    # Utility Methods
    @staticmethod
    def search_with_algorithm(text: str, pattern: str, algorithm: str) -> List[int]:
        """
        Generic search method that dispatches to the appropriate algorithm
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            algorithm: Algorithm to use ('kmp', 'bm', 'boyer_moore')
            
        Returns:
            List of match positions
        """
        algorithm = algorithm.lower()
        
        if algorithm in ['kmp', 'knuth_morris_pratt']:
            return StringMatcher.kmp_search(text, pattern)
        elif algorithm in ['bm', 'boyer_moore', 'boyermoore']:
            return StringMatcher.boyer_moore_search(text, pattern)
        else:
            # Default to KMP
            return StringMatcher.kmp_search(text, pattern)
    
    @staticmethod
    def get_algorithm_stats(text: str, pattern: str, algorithm: str) -> dict:
        """
        Get performance statistics for a specific algorithm
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            algorithm: Algorithm to use
            
        Returns:
            Dictionary with performance metrics
        """
        algorithm = algorithm.lower()
        
        if algorithm in ['kmp', 'knuth_morris_pratt']:
            return KMPSearch.search_with_stats(text, pattern)
        elif algorithm in ['bm', 'boyer_moore', 'boyermoore']:
            return BoyerMooreSearch.search_with_stats(text, pattern)
        else:
            # Default to KMP
            return KMPSearch.search_with_stats(text, pattern)
    
    @staticmethod
    def fuzzy_search(text: str, pattern: str, threshold: float = 80.0) -> List[tuple]:
        """
        Fuzzy search using Levenshtein distance
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            threshold: Similarity threshold (0-100)
            
        Returns:
            List of tuples (word, similarity_score, position)
        """
        words = text.split()
        matches = []
        
        current_pos = 0
        for word in words:
            similarity = LevenshteinDistance.calculate_similarity(pattern, word)
            if similarity >= threshold:
                matches.append((word, similarity, current_pos))
            current_pos += len(word) + 1  # +1 for space
        
        return matches

# Backward compatibility - export individual classes
__all__ = [
    'StringMatcher',
    'KMPSearch', 
    'BoyerMooreSearch',
    'AhoCorasickSearch', 
    'LevenshteinDistance'
]
