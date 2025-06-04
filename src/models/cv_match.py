from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CVMatch:
    filename: str
    similarity_score: float
    matched_keywords: List[str]
    algorithm_used: str
    full_text: str
    
    lowercase_text: str = ""        # For case-insensitive search
    keywords_only: str = ""         # Only meaningful keywords
    
    match_positions: List[int] = None
    total_matches: int = 0
    
    def __post_init__(self):
        if self.match_positions is None:
            self.match_positions = []