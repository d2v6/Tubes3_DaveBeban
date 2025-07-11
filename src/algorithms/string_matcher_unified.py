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
    # KMP Methods
    @staticmethod
    def kmp_search(text: str, pattern: str) -> List[int]:
        return KMPSearch.search(text, pattern)
    
    # Boyer-Moore Methods
    @staticmethod
    def boyer_moore_search(text: str, pattern: str) -> List[int]:
        return BoyerMooreSearch.search(text, pattern)
    
    # Aho-Corasick Methods
    @staticmethod
    def aho_corasick_search(text: str, patterns: List[str]) -> Dict[str, List[int]]:
        return AhoCorasickSearch.search(text, patterns)
    
    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        return LevenshteinDistance.calculate_similarity(s1, s2)
    
    @staticmethod
    def fuzzy_search(text: str, pattern: str, threshold: float = 80.0) -> List[tuple]:
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
