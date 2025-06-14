import re
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

@dataclass
class CVSummary:
    """Data class to store extracted CV information."""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    address: str = ""
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[Dict[str, str]] = field(default_factory=list)
    education: List[Dict[str, str]] = field(default_factory=list)

class CVExtractor:
    """Utility class for extracting structured information from CV text."""
    
    @staticmethod
    def extract_application_role(text: str) -> str:
        """
        Extract application_role from CV text.
        
        Args:
            text: Raw CV text content
            
        Returns:
            Tuple containing application_role
        """
        lines = text.split('\n')
        application_role = lines[0].strip
        
        return application_role
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract skills from CV text using enhanced pattern matching.
        
        Args:
            text: Raw CV text content
            
        Returns:
            List of unique skills (max 20)
        """
        skills = set()  # Use set to avoid duplicates
        
        # Enhanced patterns to find skills sections
        patterns = [
            r'(?i)(?:skills?|competencies|technical skills|core competencies)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+|\n[A-Z]{2,})',
            r'(?i)(?:technologies|tools|programming languages)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+)',
            r'(?i)(?:expertise|specialties)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Split skills by common delimiters including bullets
                skill_list = re.split(r'[,;•▪\n\-]+', match)
                # Enhanced filtering: remove empty, too short, too long, or common words
                filtered_skills = [
                    s.strip() for s in skill_list 
                    if s.strip() and 2 < len(s.strip()) < 50 and 
                    not s.strip().lower() in ['and', 'or', 'with', 'using', 'including']
                ]
                skills.update(filtered_skills)
        
        # Remove duplicates and sort
        unique_skills = []
        seen = set()
        for skill in skills:
            if skill.lower() not in seen:
                unique_skills.append(skill)
                seen.add(skill.lower())
        
        return sorted(unique_skills)[:20]  # Return max 20 skills, sorted

    @staticmethod
    def extract_experience(text: str) -> List[Dict[str, str]]:
        """
        Extract work experience with enhanced date and position patterns.
        
        Args:
            text: Raw CV text content
            
        Returns:
            List of experience dictionaries (max 5)
        """
        experiences = []
        
        # Enhanced patterns for different date formats in experience
        patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4}|present|current)\s*[:\n]\s*([^\n]+)',  # Year format
            r'(\d{1,2}\/\d{4})\s*[-–]\s*(\d{1,2}\/\d{4}|present|current)\s*[:\n]\s*([^\n]+)',  # Month/Year
            r'(\d{1,2}\/\d{2,4})\s*[-–]\s*(\d{1,2}\/\d{2,4}|present|current)\s*[:\s]*([^\n]+)',  # Full date
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s*[-–]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s*[:\s]*([^\n]+)'  # Month Year
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:  # Ensure we have start, end, position
                    # Handle different match lengths
                    if len(match) == 3:
                        start_date, end_date, position = match
                    elif len(match) == 5:  # Month Year format
                        start_date = f"{match[0]} {match[1]}"
                        end_date = f"{match[2]} {match[3]}"
                        position = match[4]
                    else:
                        continue
                    
                    # Filter out very short position descriptions
                    if len(position.strip()) > 5:  
                        experiences.append({
                            'start_date': start_date,
                            'end_date': end_date,
                            'position': position.strip()
                        })
        
        return experiences[:5]  # Return max 5 experiences

    @staticmethod
    def extract_education(text: str) -> List[Dict[str, str]]:
        """
        Extract education information with enhanced institution detection.
        
        Args:
            text: Raw CV text content
            
        Returns:
            List of education dictionaries (max 3)
        """
        education = []
        
        # Enhanced patterns for education entries
        edu_patterns = [
            r'(\d{4})\s*[:\-]\s*(bachelor|master|phd|diploma|[^,\n]*(?:university|college|institute|school)[^,\n]*)',
            r'(\d{4})\s*[:\-]\s*([A-Za-z\s&.]+(?:University|College|Institute|School))\s*([A-Za-z\s,]*)',
            r'([A-Za-z\s&.]+(?:University|College|Institute|School))\s*[,\s]*(\d{4})\s*([A-Za-z\s,]*)'
        ]
        
        for pattern in edu_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    # Determine which element is year vs institution/degree
                    year = ""
                    degree_info = ""
                    
                    for element in match:
                        if element.isdigit() and len(element) == 4:
                            year = element
                        elif element.strip():
                            degree_info = element.strip().title()
                    
                    if year and degree_info:
                        education.append({
                            'year': year,
                            'degree': degree_info
                        })
        
        # Remove duplicates based on year and degree
        unique_education = []
        seen = set()
        for edu in education:
            key = (edu['year'], edu['degree'].lower())
            if key not in seen:
                unique_education.append(edu)
                seen.add(key)
        
        return unique_education[:3]  # Return max 3 education entries

    @staticmethod
    def extract_summary(text: str) -> str:
        """
        Extract professional summary with enhanced patterns.
        
        Args:
            text: Raw CV text content
            
        Returns:
            Summary text (max 300 characters)
        """
        # Enhanced patterns to find summary sections
        patterns = [
            r'(?i)(?:summary|objective|profile|professional summary)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+)',
            r'(?i)(?:about|overview|career objective)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+)',
            r'(?i)(?:personal statement)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                # Clean up whitespace and limit length
                summary = re.sub(r'\s+', ' ', match.group(1).strip())
                if len(summary) > 20:  # Ensure meaningful content
                    return summary[:300]  # Limit to 300 characters
        
        # Fallback: use first substantial paragraph
        paragraphs = text.split('\n\n')
        for para in paragraphs[:5]:
            para = para.strip()
            if (50 < len(para) < 400 and 
                not any(keyword in para.lower() for keyword in ['skills', 'experience', 'education', 'phone', 'email'])):
                return para[:300]
        
        return ""

    @staticmethod
    def extract_full_summary(text: str) -> CVSummary:
        """
        Extract all CV information and return as CVSummary object.
        
        Args:
            text: Raw CV text content
            
        Returns:
            CVSummary object containing all extracted information
        """
        # Extract contact information (returns first_name, last_name, phone, address)
        first_name, last_name, phone, address = CVExtractor.extract_contact_info(text)
        
        # Create and return complete CV summary
        return CVSummary(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,  # Now properly filled
            summary=CVExtractor.extract_summary(text),
            skills=CVExtractor.extract_skills(text),
            experience=CVExtractor.extract_experience(text),
            education=CVExtractor.extract_education(text)
        )