from typing import List

class BoyerMooreSearch:
    """
    Boyer-Moore String Matching Algorithm
    
    Efficient single-pattern string matching with optimal average-case performance
    Uses Bad Character and Good Suffix heuristics for intelligent skipping
    """
    
    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
        """
        Search for pattern in text using Boyer-Moore algorithm
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            
        Returns:
            List of starting positions where pattern is found
        """
        def bad_char_heuristic(pattern):
            """Create bad character lookup table"""
            bad_char = {}
            for i in range(len(pattern)):
                bad_char[pattern[i]] = i
            return bad_char
        
        def good_suffix_heuristic(pattern):
            """Create good suffix shift table"""
            m = len(pattern)
            suffix = [0] * m
            good_suffix = [0] * m
            
            # Initialize all shifts to pattern length
            for i in range(m):
                good_suffix[i] = m
            
            # Preprocessing for case 1: suffix occurs elsewhere in pattern
            def compute_suffix_array():
                suffix[m - 1] = m
                g = m - 1
                f = 0
                
                for i in range(m - 2, -1, -1):
                    if i > g and suffix[i + m - 1 - f] < i - g:
                        suffix[i] = suffix[i + m - 1 - f]
                    else:
                        if i < g:
                            g = i
                        f = i
                        while g >= 0 and pattern[g] == pattern[g + m - 1 - f]:
                            g -= 1
                        suffix[i] = f - g
                return suffix
            
            suffix = compute_suffix_array()
            
            # Case 1: The suffix occurs elsewhere in the pattern
            j = 0
            for i in range(m - 1, -1, -1):
                if suffix[i] == i + 1:
                    while j < m - 1 - i:
                        if good_suffix[j] == m:
                            good_suffix[j] = m - 1 - i
                        j += 1
            
            # Case 2: A prefix of the pattern matches a suffix of the good suffix
            for i in range(m - 1):
                good_suffix[m - 1 - suffix[i]] = m - 1 - i
            
            return good_suffix
        
        # Input validation
        if not pattern or not text:
            return []
        
        # Case normalization    
        text = text.lower()
        pattern = pattern.lower()
        
        # Preprocessing both heuristics
        bad_char = bad_char_heuristic(pattern)
        good_suffix = good_suffix_heuristic(pattern)
        
        matches = []
        shift = 0
        
        # Main search loop
        while shift <= len(text) - len(pattern):
            # Compare from right to left (Boyer-Moore signature)
            j = len(pattern) - 1
            
            # Match characters from right to left
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1
            
            # Check if we found a complete match
            if j < 0:
                # MATCH FOUND
                matches.append(shift)
                
                # Use good suffix heuristic for shift after match
                shift += good_suffix[0]
            else:
                # MISMATCH: Use maximum of both heuristics
                mismatched_char = text[shift + j]
                
                # Bad character shift
                bad_char_shift = j - bad_char.get(mismatched_char, -1)
                
                # Good suffix shift
                good_suffix_shift = good_suffix[j]
                
                # Take maximum shift for optimal performance
                shift += max(bad_char_shift, good_suffix_shift, 1)
        
        return matches
    
    @staticmethod
    def search_with_stats(text: str, pattern: str) -> dict:
        """
        Boyer-Moore search with performance statistics
        
        Returns:
            Dictionary with matches and performance metrics
        """
        import time
        
        start_time = time.time()
        matches = BoyerMooreSearch.search(text, pattern)
        end_time = time.time()
        
        return {
            'matches': matches,
            'total_matches': len(matches),
            'pattern_length': len(pattern),
            'text_length': len(text),
            'time_taken': end_time - start_time,
            'algorithm': 'Boyer-Moore'
        }
