from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List


@dataclass
class ApplicantProfile:
    applicant_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else "Unknown"


@dataclass
class ApplicationDetail:
    detail_id: Optional[int] = None
    applicant_id: Optional[int] = None
    application_role: Optional[str] = None
    cv_path: Optional[str] = None
    applied_date: Optional[datetime] = None
    status: Optional[str] = "active"

    # Related data
    applicant_profile: Optional[ApplicantProfile] = None


@dataclass
class CVSearchResult:
    applicant_profile: ApplicantProfile
    application_detail: ApplicationDetail
    match_count: int = 0
    matched_keywords: List[str] = None
    similarity_score: float = 0.0
    cv_text: str = ""

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []
