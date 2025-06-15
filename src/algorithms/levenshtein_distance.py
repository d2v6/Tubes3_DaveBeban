class LevenshteinDistance:
    """
    Levenshtein Distance Algorithm for String Similarity
    
    Calculates edit distance between two strings using dynamic programming
    Useful for fuzzy string matching and similarity calculations
    """
    
    @staticmethod
    def calculate_distance(s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Integer representing the minimum edit distance
        """
        if len(s1) < len(s2):
            return LevenshteinDistance.calculate_distance(s2, s1)
        
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
        """
        Calculate similarity percentage using Levenshtein distance
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Float representing similarity percentage (0-100)
        """
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 100.0
        
        distance = LevenshteinDistance.calculate_distance(s1.lower(), s2.lower())
        similarity = ((max_len - distance) / max_len) * 100
        return similarity
    
    @staticmethod
    def similarity_with_stats(s1: str, s2: str) -> dict:
        """
        Calculate similarity with detailed statistics
        
        Returns:
            Dictionary with similarity metrics and performance data
        """
        import time
        
        start_time = time.time()
        distance = LevenshteinDistance.calculate_distance(s1, s2)
        similarity = LevenshteinDistance.calculate_similarity(s1, s2)
        end_time = time.time()
        
        return {
            'distance': distance,
            'similarity_percentage': similarity,
            'string1_length': len(s1),
            'string2_length': len(s2),
            'max_length': max(len(s1), len(s2)),
            'time_taken': end_time - start_time,
            'algorithm': 'Levenshtein'
        }
    
    @staticmethod
    def is_similar(s1: str, s2: str, threshold: float = 80.0) -> bool:
        """
        Check if two strings are similar above a given threshold
        
        Args:
            s1: First string
            s2: Second string
            threshold: Similarity threshold percentage (default 80%)
            
        Returns:
            Boolean indicating if strings are similar above threshold
        """
        similarity = LevenshteinDistance.calculate_similarity(s1, s2)
        return similarity >= threshold
