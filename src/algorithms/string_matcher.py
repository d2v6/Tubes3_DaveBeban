from typing import List, Dict, Set, Tuple
from collections import deque

class TrieNode:
    """Node for Aho-Corasick trie structure"""
    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []
        self.is_end = False

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
    def aho_corasick_search(text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """
        AHO-CORASICK: Multi-pattern string matching algorithm
        
        Efficiently searches for multiple patterns simultaneously in O(n + m + z) time
        where n = text length, m = total pattern lengths, z = number of matches
        
        Args:
            text: Text to search in
            patterns: List of patterns to search for
            
        Returns:
            Dictionary mapping each pattern to list of match positions
        """
        if not text or not patterns:
            return {}
        
        # Normalize inputs
        text = text.lower()
        patterns = [p.lower().strip() for p in patterns if p.strip()]
        
        if not patterns:
            return {}
        
        # Build Aho-Corasick automaton
        root = StringMatcher._build_aho_corasick_automaton(patterns)
        
        # Search for all patterns simultaneously
        matches = {pattern: [] for pattern in patterns}
        current_node = root
        
        for i, char in enumerate(text):
            # Find the next state (follow failure links if needed)
            while current_node and char not in current_node.children:
                current_node = current_node.failure
            
            if current_node is None:
                current_node = root
                continue
            
            current_node = current_node.children[char]
            
            # Check for pattern matches at current position
            temp_node = current_node
            while temp_node:
                for pattern in temp_node.output:
                    match_start = i - len(pattern) + 1
                    matches[pattern].append(match_start)
                temp_node = temp_node.failure
        
        return matches
    
    @staticmethod
    def _build_aho_corasick_automaton(patterns: List[str]) -> TrieNode:
        """BUILD: Construct Aho-Corasick automaton (trie + failure function)"""
        root = TrieNode()
        root.failure = root
        
        # Phase 1: Build trie from patterns
        for pattern in patterns:
            current = root
            for char in pattern:
                if char not in current.children:
                    current.children[char] = TrieNode()
                current = current.children[char]
            current.is_end = True
            current.output.append(pattern)
        
        # Phase 2: Build failure function using BFS
        queue = deque()
        
        # Initialize failure links for first level (direct children of root)
        for child in root.children.values():
            child.failure = root
            queue.append(child)
        
        # Build failure links for deeper levels
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link for this child
                failure_node = current.failure
                while failure_node != root and char not in failure_node.children:
                    failure_node = failure_node.failure
                
                if char in failure_node.children and failure_node.children[char] != child:
                    child.failure = failure_node.children[char]
                else:
                    child.failure = root
                
                # Copy output from failure node (for overlapping patterns)
                child.output.extend(child.failure.output)
        
        return root
    
    @staticmethod
    def aho_corasick_with_stats(text: str, patterns: List[str]) -> Dict:
        """
        AHO-CORASICK WITH STATS: Enhanced version with performance metrics
        
        Returns detailed statistics about the multi-pattern search
        """
        import time
        
        if not text or not patterns:
            return {
                'matches': {},
                'total_matches': 0,
                'patterns_found': 0,
                'time_taken': 0,
                'automaton_size': 0
            }
        
        start_time = time.time()
        
        # Clean patterns
        clean_patterns = [p.lower().strip() for p in patterns if p.strip()]
        
        # Build automaton and count nodes
        root = StringMatcher._build_aho_corasick_automaton(clean_patterns)
        automaton_size = StringMatcher._count_automaton_nodes(root)
        
        # Perform search
        matches = StringMatcher.aho_corasick_search(text, clean_patterns)
        
        end_time = time.time()
        
        # Calculate statistics
        total_matches = sum(len(positions) for positions in matches.values())
        patterns_found = sum(1 for positions in matches.values() if positions)
        
        return {
            'matches': matches,
            'total_matches': total_matches,
            'patterns_found': patterns_found,
            'total_patterns': len(clean_patterns),
            'time_taken': end_time - start_time,
            'automaton_size': automaton_size,
            'text_length': len(text),
            'match_density': total_matches / len(text) if text else 0
        }
    
    @staticmethod
    def _count_automaton_nodes(root: TrieNode) -> int:
        """ COUNT: Count total nodes in Aho-Corasick automaton"""
        if not root:
            return 0
        
        count = 1
        for child in root.children.values():
            count += StringMatcher._count_automaton_nodes(child)
        return count
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return StringMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        """Calculate similarity percentage using Levenshtein distance"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 100.0
        
        distance = StringMatcher.levenshtein_distance(s1.lower(), s2.lower())
        similarity = ((max_len - distance) / max_len) * 100
        return similarity