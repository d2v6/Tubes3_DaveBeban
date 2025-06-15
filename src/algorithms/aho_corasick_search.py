from typing import List, Dict
from collections import deque


class TrieNode:
    """Node for Aho-Corasick trie structure"""

    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []
        self.is_end = False


class AhoCorasickSearch:
    """
    Aho-Corasick Multi-Pattern String Matching Algorithm

    Efficiently searches for multiple patterns simultaneously in O(n + m + z) time
    where n = text length, m = total pattern lengths, z = number of matches
    """

    @staticmethod
    def search(text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """
        Search for multiple patterns in text using Aho-Corasick algorithm

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
        root = AhoCorasickSearch._build_automaton(patterns)

        # Search for all patterns simultaneously
        matches = {pattern: [] for pattern in patterns}
        current_node = root

        for i, char in enumerate(text):
            # Find the next state (follow failure links if needed)
            # Keep following failure links until we find a match or reach root
            while current_node is not root and char not in current_node.children:
                current_node = current_node.failure

            # If we found the character, move to that child
            if char in current_node.children:
                current_node = current_node.children[char]
            else:
                # If even root doesn't have this character, stay at root
                current_node = root
                continue

            # Check for pattern matches at current position
            temp_node = current_node
            while temp_node is not root:
                for pattern in temp_node.output:
                    match_start = i - len(pattern) + 1
                    matches[pattern].append(match_start)
                temp_node = temp_node.failure

            # Also check root's output (for patterns that are single characters)
            for pattern in root.output:
                match_start = i - len(pattern) + 1
                matches[pattern].append(match_start)

        return matches

    @staticmethod
    def _build_automaton(patterns: List[str]) -> TrieNode:
        """Build Aho-Corasick automaton (trie + failure function)"""
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
