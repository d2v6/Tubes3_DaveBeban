from typing import List

class StringMatcher:
    @staticmethod
    def kmp_search(text: str, pattern: str) -> List[int]:
        def compute_lps(pattern):
            lps = [0] * len(pattern)
            length = 0
            i = 1
            
            while i < len(pattern):
                if pattern[i] == pattern[length]:
                    length += 1
                    lps[i] = length
                    i += 1
                else:
                    if length != 0:
                        length = lps[length - 1]
                    else:
                        lps[i] = 0
                        i += 1
            return lps
        
        if not pattern:
            return []
            
        text = text.lower()
        pattern = pattern.lower()
        
        lps = compute_lps(pattern)
        matches = []
        i = j = 0
        
        while i < len(text):
            if pattern[j] == text[i]:
                i += 1
                j += 1
                
            if j == len(pattern):
                matches.append(i - j)
                j = lps[j - 1]
            elif i < len(text) and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        
        return matches
    
    @staticmethod
    def boyer_moore_search(text: str, pattern: str) -> List[int]:
        """Boyer-Moore algorithm with both Bad Character and Good Suffix heuristics"""
        
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
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return StringMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        
        return prev_row[-1]
    
    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        """Calculate similarity percentage using Levenshtein distance"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 100.0
        
        distance = StringMatcher.levenshtein_distance(s1.lower(), s2.lower())
        similarity = ((max_len - distance) / max_len) * 100
        return similarity