from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Tuple, Dict


@dataclass
class ApplicantProfile:
    applicant_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None

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
    applicant_profile: Optional[ApplicantProfile] = None


@dataclass
class CVSearchResult:
    applicant_profile: ApplicantProfile
    application_detail: ApplicationDetail
    matched_keywords: List[Tuple[str, int]] = field(default_factory=list)
    cv_text: str = ""
    search_timing: Dict[str, float] = field(default_factory=dict)

    @property
    def total_matches(self) -> int:
        """Get total number of matches across all keywords"""
        return sum(count for _, count in self.matched_keywords)

    @property
    def number_of_matches(self) -> int:
        """Alias for total_matches for backward compatibility"""
        return self.total_matches
