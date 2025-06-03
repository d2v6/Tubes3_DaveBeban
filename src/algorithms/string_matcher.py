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
        """Boyer-Moore algorithm for pattern matching"""
        def bad_char_heuristic(pattern):
            bad_char = {}
            for i in range(len(pattern)):
                bad_char[pattern[i]] = i
            return bad_char
        
        if not pattern:
            return []
            
        text = text.lower()
        pattern = pattern.lower()
        
        bad_char = bad_char_heuristic(pattern)
        matches = []
        shift = 0
        
        while shift <= len(text) - len(pattern):
            j = len(pattern) - 1
            
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1
                
            if j < 0:
                matches.append(shift)
                shift += (len(pattern) - bad_char.get(text[shift + len(pattern)], -1) - 1 
                         if shift + len(pattern) < len(text) else 1)
            else:
                shift += max(1, j - bad_char.get(text[shift + j], -1))
        
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