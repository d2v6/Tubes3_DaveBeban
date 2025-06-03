from dataclasses import dataclass
from typing import List

@dataclass
class CVMatch:
    filename: str
    similarity_score: float
    matched_keywords: List[str]
    algorithm_used: str
    full_text: str