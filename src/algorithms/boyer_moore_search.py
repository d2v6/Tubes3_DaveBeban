from typing import List

class BoyerMooreSearch:
    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
        def bad_char_heuristic(pattern):
            bad_char = {}
            for i in range(len(pattern)):
                bad_char[pattern[i]] = i
            return bad_char
        
        def good_suffix_heuristic(pattern):
            m = len(pattern)
            suffix = [0] * m
            good_suffix = [0] * m
            
            for i in range(m):
                good_suffix[i] = m
            
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
            
            j = 0
            for i in range(m - 1, -1, -1):
                if suffix[i] == i + 1:
                    while j < m - 1 - i:
                        if good_suffix[j] == m:
                            good_suffix[j] = m - 1 - i
                        j += 1
            
            for i in range(m - 1):
                good_suffix[m - 1 - suffix[i]] = m - 1 - i
            
            return good_suffix
        
        if not pattern or not text:
            return []
        
        text = text.lower()
        pattern = pattern.lower()
        
        bad_char = bad_char_heuristic(pattern)
        good_suffix = good_suffix_heuristic(pattern)
        
        matches = []
        shift = 0
        
        while shift <= len(text) - len(pattern):
            j = len(pattern) - 1
            
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1
            
            if j < 0:
                matches.append(shift)
                
                shift += good_suffix[0]
            else:
                mismatched_char = text[shift + j]
                
                bad_char_shift = j - bad_char.get(mismatched_char, -1)
                
                good_suffix_shift = good_suffix[j]
                
                shift += max(bad_char_shift, good_suffix_shift, 1)
        
        return matches
    
    @staticmethod
    def search_with_stats(text: str, pattern: str) -> dict:
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
