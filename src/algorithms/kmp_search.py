from typing import List

class KMPSearch:
    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
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
    def search_with_stats(text: str, pattern: str) -> dict:
        import time
        
        start_time = time.time()
        matches = KMPSearch.search(text, pattern)
        end_time = time.time()
        
        return {
            'matches': matches,
            'total_matches': len(matches),
            'pattern_length': len(pattern),
            'text_length': len(text),
            'time_taken': end_time - start_time,
            'algorithm': 'KMP'
        }
