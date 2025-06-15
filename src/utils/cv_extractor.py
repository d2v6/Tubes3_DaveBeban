import re
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field

class SectionBoundary(NamedTuple):
    """Information about detected section boundary"""
    section_type: str
    start_line: int
    end_line: int
    content: str
    detection_confidence: float

@dataclass
class CVSummary:
    """Data class to store extracted CV information."""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    address: str = ""
    date_of_birth: str = ""
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[Dict[str, str]] = field(default_factory=list)
    education: List[Dict[str, str]] = field(default_factory=list)

class DynamicCVExtractor:
    """Dynamic CV extractor with flexible section detection"""
    
    def __init__(self):
        self.section_detectors = {
            'summary': {
                'patterns': [
                    r'(?i)\b(summary|profile|overview|objective|about)\b',
                    r'(?i)\b(professional\s+summary|career\s+summary|executive\s+summary)\b',
                    r'(?i)\b(personal\s+statement|career\s+objective|professional\s+profile)\b',
                    r'(?i)\b(introduction|background|bio)\b'
                ],
                'weight': 1.0
            },
            'skills': {
                'patterns': [
                    r'(?i)\b(skills?|competencies|proficiencies|expertise)\b',
                    r'(?i)\b(technical\s+skills?|core\s+competencies|key\s+skills?)\b',
                    r'(?i)\b(highlights|strengths|abilities|capabilities)\b',
                    r'(?i)\b(technologies|tools|software|programming)\b',
                    r'(?i)\b(skill\s+set|technical\s+expertise)\b'
                ],
                'weight': 1.0
            },
            'experience': {
                'patterns': [
                    r'(?i)\b(experience|employment|career|work)\b',
                    r'(?i)\b(work\s+(experience|history|background))\b',
                    r'(?i)\b(professional\s+(experience|background|history))\b',
                    r'(?i)\b(employment\s+history|career\s+history)\b',
                    r'(?i)\b(positions|jobs|roles)\b'
                ],
                'weight': 1.0
            },
            'education': {
                'patterns': [
                    r'(?i)\b(education|qualifications|academic)\b',
                    r'(?i)\b(educational\s+background|academic\s+background)\b',
                    r'(?i)\b(academic\s+qualifications|degrees|schooling)\b',
                    r'(?i)\b(certifications|training|learning)\b',
                    r'(?i)\b(university|college|school)\b'
                ],
                'weight': 1.0
            }
        }
        
        # Date patterns for experience validation
        self.date_patterns = [
            r'([A-Za-z]+\s+\d{4}\s+(?:to|[-–—])\s+[A-Za-z]+\s+\d{4})',
            r'([A-Za-z]+\s+\d{4}\s*[-–—]\s*[A-Za-z]+\s+\d{4})',
            r'(\d{4}\s*[-–—]\s*\d{4})',
            r'(\d{4}\s+(?:to|[-–—])\s+\d{4})',
            r'(\d{4}\s*[-–—]\s*(?:Present|Current|Now))',
            r'(\d{4}\s+(?:to|[-–—])\s+(?:Present|Current|Now))',
            r'(\d{1,2}/\d{4}\s*[-–—]\s*\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{4}\s*[-–—]\s*(?:Present|Current))',
            r'([A-Za-z]+\s+\d{4})',
        ]
        
        # Degree patterns for education validation
        self.degree_patterns = [
            r'(?i)\b(Bachelor|Master|Associate|PhD|Doctorate|Certificate|Diploma)\b',
            r'(?i)\b(B\.?[AS]\.?|M\.?[AS]\.?|Ph\.?D\.?|MBA|MSc|BSc|B\.?Sc\.?|M\.?Sc\.?)\b',
            r'(?i)\b(Bachelors?|Masters?|Associates?|Doctoral)\b'
        ]

    def detect_all_sections(self, text: str) -> List[SectionBoundary]:
        """Detect all sections dynamically throughout the document"""
        lines = text.split('\n')
        detected_sections = []
        
        # Step 1: Find all potential section headers
        section_candidates = []
        
        for line_idx, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 3:
                continue
            
            # Check each section type
            for section_type, detector in self.section_detectors.items():
                confidence = self._calculate_line_section_confidence(line_clean, section_type)
                
                if confidence > 0.3:  # Threshold untuk deteksi section
                    section_candidates.append({
                        'line_idx': line_idx,
                        'section_type': section_type,
                        'confidence': confidence,
                        'line_text': line_clean
                    })
        
        # Step 2: Resolve conflicts and finalize sections
        finalized_sections = self._resolve_section_conflicts(section_candidates)
        
        # Step 3: Extract content for each section
        for i, section in enumerate(finalized_sections):
            start_line = section['line_idx'] + 1  # Skip header line
            
            # Find end line (next section start or end of document)
            if i + 1 < len(finalized_sections):
                end_line = finalized_sections[i + 1]['line_idx']
            else:
                end_line = len(lines)
            
            # Extract content
            content_lines = []
            for line_idx in range(start_line, end_line):
                if line_idx < len(lines):
                    line = lines[line_idx].strip()
                    if line:  # Skip empty lines
                        content_lines.append(line)
            
            content = '\n'.join(content_lines)
            
            # Validate content and adjust confidence
            final_confidence = self._validate_section_content(section['section_type'], content, section['confidence'])
            
            if final_confidence > 0.2:  # Only keep sections with reasonable confidence
                detected_sections.append(SectionBoundary(
                    section_type=section['section_type'],
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    detection_confidence=final_confidence
                ))
        
        return detected_sections

    def _calculate_line_section_confidence(self, line: str, section_type: str) -> float:
        """Calculate confidence that a line is a section header"""
        confidence = 0.0
        line_lower = line.lower().strip()
        detector = self.section_detectors[section_type]
        
        # Skip very long lines (unlikely to be headers)
        if len(line) > 80:
            return 0.0
          # Skip lines with email addresses, phone numbers, or URLs
        if any(pattern in line_lower for pattern in ['@', 'http', 'www', '+1', '(555)', 'phone:', 'email:']):
            return 0.0
        
        # Check patterns
        for pattern in detector['patterns']:
            if re.search(pattern, line):
                # Check if this looks like a section header
                
                # Boost for short lines (more likely headers)
                length_factor = max(0.3, 1.0 - (len(line) / 50))
                
                # Boost for lines that are mostly uppercase or title case
                title_case_boost = 0.0
                if line.isupper() or line.istitle():
                    title_case_boost = 0.3
                
                # Boost for standalone section words
                keyword_match = re.search(pattern, line)
                if keyword_match:
                    keyword_ratio = len(keyword_match.group()) / len(line.strip())
                    # High boost if the keyword makes up most of the line
                    if keyword_ratio > 0.6:
                        standalone_boost = 0.4
                    elif keyword_ratio > 0.3:
                        standalone_boost = 0.2
                    else:
                        standalone_boost = 0.0
                else:
                    standalone_boost = 0.0
                
                # Penalize lines with bullet points or too much detail
                detail_penalty = 0.0
                if any(char in line for char in ['•', '▪', '-', '1.', '2.', '3.']):
                    detail_penalty = 0.3
                if any(word in line_lower for word in ['responsibilities', 'developed', 'managed', 'implemented']):
                    detail_penalty = 0.4
                
                pattern_confidence = (detector['weight'] * length_factor + 
                                    title_case_boost + standalone_boost - detail_penalty)
                confidence = max(confidence, pattern_confidence)
        
        # Boost confidence for exact matches to common section names
        standalone_keywords = {
            'summary': ['summary', 'profile', 'overview', 'objective', 'professional summary'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'experience': ['experience', 'work experience', 'employment', 'professional experience'],
            'education': ['education', 'academic background', 'qualifications']
        }
        
        if section_type in standalone_keywords:
            for keyword in standalone_keywords[section_type]:
                if line_lower == keyword or line_lower == keyword.upper():
                    confidence = max(confidence, 0.95)
                elif line_lower.startswith(keyword) and len(line) < 35:
                    confidence = max(confidence, 0.85)
        
        return min(confidence, 1.0)

    def _resolve_section_conflicts(self, candidates: List[Dict]) -> List[Dict]:
        """Resolve conflicts when multiple sections detected on same line"""
        # Sort by line index
        candidates.sort(key=lambda x: x['line_idx'])
        
        finalized = []
        used_lines = set()
        
        # Group by line index
        lines_dict = {}
        for candidate in candidates:
            line_idx = candidate['line_idx']
            if line_idx not in lines_dict:
                lines_dict[line_idx] = []
            lines_dict[line_idx].append(candidate)
        
        # Process each line
        for line_idx in sorted(lines_dict.keys()):
            line_candidates = lines_dict[line_idx]
            
            if len(line_candidates) == 1:
                # No conflict
                finalized.append(line_candidates[0])
            else:
                # Conflict: choose highest confidence
                best_candidate = max(line_candidates, key=lambda x: x['confidence'])
                finalized.append(best_candidate)
        
        return finalized

    def _validate_section_content(self, section_type: str, content: str, initial_confidence: float) -> float:
        """Validate and adjust confidence based on content analysis"""
        if not content:
            return 0.0
        
        content_lower = content.lower()
        confidence = initial_confidence
        
        # Section-specific validation
        if section_type == 'summary':
            # Look for summary-like content
            summary_indicators = ['professional', 'experienced', 'expert', 'skilled', 'specializing', 'years', 'background']
            matches = sum(1 for indicator in summary_indicators if indicator in content_lower)
            if matches >= 2:
                confidence += 0.2
            elif len(content) > 100:  # Long descriptive text
                confidence += 0.1
                
        elif section_type == 'skills':
            # Look for skill-like patterns
            if any(sep in content for sep in [',', ';', '•', '▪', '-']):
                confidence += 0.3
            
            skill_indicators = ['programming', 'software', 'management', 'analysis', 'development', 'microsoft', 'java', 'python']
            matches = sum(1 for indicator in skill_indicators if indicator in content_lower)
            if matches >= 1:
                confidence += 0.2
                
        elif section_type == 'experience':
            # Look for experience patterns
            date_matches = sum(1 for pattern in self.date_patterns if re.search(pattern, content))
            if date_matches >= 1:
                confidence += 0.3
            
            exp_indicators = ['company', 'position', 'role', 'responsibilities', 'managed', 'developed', 'implemented']
            matches = sum(1 for indicator in exp_indicators if indicator in content_lower)
            if matches >= 2:
                confidence += 0.2
                
        elif section_type == 'education':
            # Look for education patterns
            degree_matches = sum(1 for pattern in self.degree_patterns if re.search(pattern, content))
            if degree_matches >= 1:
                confidence += 0.4
            
            edu_indicators = ['university', 'college', 'school', 'degree', 'graduation', 'gpa']
            matches = sum(1 for indicator in edu_indicators if indicator in content_lower)
            if matches >= 1:
                confidence += 0.2
        
        return min(confidence, 1.0)

    def extract_summary(self, section_boundary: SectionBoundary) -> str:
        """Extract and clean summary content"""
        if not section_boundary or section_boundary.detection_confidence < 0.3:
            return ""
        
        content = section_boundary.content
        # Clean whitespace and format
        summary = re.sub(r'\s+', ' ', content.strip())
        return summary[:500]  # Limit length

    def extract_skills(self, section_boundary: SectionBoundary) -> List[str]:
        """Extract skills with dynamic parsing"""
        if not section_boundary or section_boundary.detection_confidence < 0.2:
            return []
        
        content = section_boundary.content
        skills = []
        
        # Method 1: Comma/semicolon separated
        if ',' in content:
            potential_skills = [skill.strip() for skill in content.split(',')]
            skills.extend([s for s in potential_skills if s and 2 < len(s) < 50])
        elif ';' in content:
            potential_skills = [skill.strip() for skill in content.split(';')]
            skills.extend([s for s in potential_skills if s and 2 < len(s) < 50])
          # Method 2: Bullet points or dashes  
        elif re.search(r'[•▪\-]\s*', content):
            # First try to extract bullet point lines
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'^[•▪\-]\s*', line):
                    # This is a bullet point line - extract skills from it
                    skill_text = re.sub(r'^[•▪\-]\s*', '', line).strip()
                    
                    # Check if it has a category (like "Programming Languages:")
                    if ':' in skill_text:
                        parts = skill_text.split(':', 1)
                        if len(parts) == 2:
                            category = parts[0].strip()
                            skill_list = parts[1].strip()
                            
                            # Add category as a skill if it's meaningful
                            if len(category) > 2 and len(category) < 30:
                                skills.append(category)
                            
                            # Parse the skill list
                            if ',' in skill_list:
                                sub_skills = [s.strip() for s in skill_list.split(',') if s.strip()]
                                skills.extend(sub_skills)
                            else:
                                skills.append(skill_list)
                    else:
                        # Direct skill or skill list
                        if ',' in skill_text:
                            sub_skills = [s.strip() for s in skill_text.split(',') if s.strip()]
                            skills.extend(sub_skills)
                        else:
                            skills.append(skill_text)
        
        # Method 3: Line by line (each line is a skill or skill group)
        else:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            for line in lines:
                if len(line.split()) <= 6:  # Short lines likely to be skills
                    skills.append(line)
                else:
                    # Try to extract capitalized terms
                    cap_terms = re.findall(r'\b[A-Z][A-Za-z\s]{1,25}(?:\s+[A-Z][A-Za-z\s]{1,25})*\b', line)
                    skills.extend([term.strip() for term in cap_terms if 2 < len(term.strip()) < 30])
          # Clean and deduplicate
        cleaned_skills = []
        seen = set()
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'with', 'for', 'to', 'of', 'by', 'new', 'york', 'ny', 'ca', 'tx', 'fl'}
        location_patterns = [r'\b[A-Z]{2}\b', r'\b\d{5}\b']  # State codes and zip codes
        
        for skill in skills:
            skill = skill.strip()
            skill_lower = skill.lower()
            
            # Skip if it looks like location data
            is_location = (
                any(re.search(pattern, skill) for pattern in location_patterns) or
                skill_lower in {'new york', 'california', 'texas', 'florida', 'ny', 'ca', 'tx', 'fl'} or
                re.search(r'\b\d{5}(?:-\d{4})?\b', skill)  # ZIP codes
            )
            
            if (skill and 
                len(skill) > 2 and 
                skill_lower not in seen and
                skill_lower not in stop_words and
                not is_location):
                cleaned_skills.append(skill)
                seen.add(skill_lower)
        
        return cleaned_skills[:25]  # Increased limit

    def extract_experience(self, section_boundary: SectionBoundary) -> List[Dict[str, str]]:
        """Extract experience with comprehensive parsing"""
        if not section_boundary or section_boundary.detection_confidence < 0.3:
            return []
        
        content = section_boundary.content
        experiences = []
        lines = content.split('\n')
        
        current_job = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Look for date patterns (indicates new job)
            date_match = None
            for pattern in self.date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    break
            
            # Also check next line for dates if current line doesn't have one
            if not date_match and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                for pattern in self.date_patterns:
                    date_match = re.search(pattern, next_line)
                    if date_match:
                        # Combine current line (position/company) with next line (date)
                        line = line + " " + next_line
                        i += 1  # Skip the next line since we processed it
                        break
            
            if date_match:
                # Save previous job
                if current_job and (current_job['position'] or current_job['company']):
                    experiences.append(current_job)
                
                # Start new job
                current_job = {
                    'position': '',
                    'company': '',
                    'start_date': '',
                    'end_date': '',
                    'location': '',
                    'description': ''
                }
                
                # Parse date range
                date_range = date_match.group(1).strip()
                if any(sep in date_range for sep in [' to ', '-', '–', '—']):
                    for sep in [' to ', '–', '—', '-']:
                        if sep in date_range:
                            parts = date_range.split(sep, 1)
                            if len(parts) == 2:
                                current_job['start_date'] = parts[0].strip()
                                current_job['end_date'] = parts[1].strip()
                            break
                else:
                    current_job['start_date'] = date_range
                
                # Parse the line containing position, company, and possibly location
                line_without_date = line.replace(date_match.group(0), '').strip()
                
                # Split by common separators
                parts = []
                for sep in [' - ', ' at ', ' | ', ',']:
                    if sep in line_without_date:
                        parts = [p.strip() for p in line_without_date.split(sep) if p.strip()]
                        break
                
                if not parts:
                    parts = [line_without_date]
                
                # Assign parts to position and company
                if len(parts) >= 2:
                    current_job['position'] = parts[0]
                    current_job['company'] = parts[1]
                    if len(parts) >= 3:
                        current_job['location'] = parts[2]
                elif len(parts) == 1:
                    # Could be either position or company
                    if any(keyword in parts[0].lower() for keyword in ['engineer', 'manager', 'developer', 'analyst', 'consultant']):
                        current_job['position'] = parts[0]
                    else:
                        current_job['company'] = parts[0]
            
            elif current_job:
                # This is description or additional info
                if len(line) > 15:  # Meaningful content
                    if current_job['description']:
                        current_job['description'] += ' ' + line
                    else:
                        current_job['description'] = line
                elif not current_job['position'] and len(line) > 5:
                    # Might be position on separate line
                    current_job['position'] = line
                elif not current_job['company'] and len(line) > 5:
                    # Might be company on separate line
                    current_job['company'] = line
            
            i += 1
          # Don't forget the last job
        if current_job and (current_job['position'] or current_job['company']):
            experiences.append(current_job)
        
        return experiences[:10]  # Increased limit

    def extract_education(self, section_boundary: SectionBoundary) -> List[Dict[str, str]]:
        """Extract education with flexible parsing"""
        if not section_boundary or section_boundary.detection_confidence < 0.3:
            return []
        
        content = section_boundary.content
        education_list = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree patterns
            degree_match = None
            for pattern in self.degree_patterns:
                degree_match = re.search(pattern, line)
                if degree_match:
                    break
            
            if degree_match or any(keyword in line.lower() for keyword in ['university', 'college', 'school']):
                education_entry = {
                    'degree': '',
                    'field': '',
                    'institution': '',
                    'year': '',
                    'location': ''
                }
                
                # Extract degree
                if degree_match:
                    degree_text = degree_match.group(0)
                    # Try to get fuller degree description
                    expanded_degree = re.search(r'\b' + re.escape(degree_text) + r'[^,\d\n]*', line, re.IGNORECASE)
                    if expanded_degree:
                        education_entry['degree'] = expanded_degree.group(0).strip()
                    else:
                        education_entry['degree'] = degree_text
                
                # Extract year
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', line)
                if year_match:
                    education_entry['year'] = year_match.group(1)
                
                # Extract institution
                institution_patterns = [
                    r'\b([A-Z][A-Za-z\s&.]+(?:University|College|Institute|School))\b',
                    r'\b(University\s+of\s+[A-Za-z\s]+)\b',
                    r'\b([A-Za-z\s]+\s+University)\b'
                ]
                
                for pattern in institution_patterns:
                    inst_match = re.search(pattern, line)
                    if inst_match:
                        education_entry['institution'] = inst_match.group(1).strip()
                        break
                
                # If no institution found with patterns, try to extract from remaining text
                if not education_entry['institution']:
                    remaining = line
                    if degree_match:
                        remaining = remaining.replace(degree_match.group(0), '')
                    if year_match:
                        remaining = remaining.replace(year_match.group(0), '')
                    
                    # Look for substantial text that could be institution
                    parts = [part.strip() for part in remaining.split(',') if part.strip()]
                    for part in parts:
                        if len(part) > 10 and not part.isdigit():
                            education_entry['institution'] = part
                            break
                
                # Extract location
                loc_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2}|[A-Za-z\s]+)', line)
                if loc_match:
                    education_entry['location'] = f"{loc_match.group(1).strip()}, {loc_match.group(2).strip()}"
                
                # Only add if we have meaningful information
                if education_entry['degree'] or education_entry['institution']:
                    education_list.append(education_entry)
        
        return education_list[:5]  # Reasonable limit

    def extract_contact_info(self, text: str) -> Tuple[str, str, str, str]:
        """Extract contact information from document"""
        lines = text.split('\n')[:20]  # Check more lines
        
        first_name = ""
        last_name = ""
        phone = ""
        address = ""
        
        # Extract name - look for likely name patterns
        for line in lines:
            line = line.strip()
            if (line and 
                len(line) < 50 and  # Not too long
                not any(keyword in line.lower() for keyword in 
                    ['phone', 'email', 'address', 'cv', 'resume', '@', 'summary', 'objective']) and
                not re.search(r'\d', line)):  # No digits
                
                words = line.split()
                if 2 <= len(words) <= 4 and all(word.replace('.', '').isalpha() for word in words):
                    first_name = words[0].title()
                    last_name = " ".join(words[1:]).title()
                    break
        
        # Extract phone - multiple patterns
        phone_patterns = [
            r'(\+?\d{1,4}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            r'\+?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                phone = phone_match.group().strip()
                break
        
        # Extract address - broader patterns
        address_patterns = [
            r'(?i).*\b(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|way|circle|court|ct)\b.*',
            r'(?i).*\b\d+.*(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)\b.*',
            r'(?i).*\b(?:apartment|apt|suite|unit|floor)\s*\d+.*',
            r'(?i).*\b\d{5}(?:-\d{4})?\b.*'  # ZIP codes
        ]
        
        for line in lines:
            for pattern in address_patterns:
                if re.search(pattern, line):
                    address = line.strip()
                    break
            if address:
                break
        
        return first_name, last_name, phone, address

    @staticmethod
    def extract_full_summary(text: str, personal_info = None) -> CVSummary:
        """Main extraction method using dynamic section detection"""
        extractor = DynamicCVExtractor()
        
        # Step 1: Detect all sections dynamically
        section_boundaries = extractor.detect_all_sections(text)
          # Step 2: Organize sections by type - prefer later, more content-rich sections
        sections_by_type = {}
        for boundary in section_boundaries:
            section_type = boundary.section_type
            if section_type not in sections_by_type:
                sections_by_type[section_type] = boundary
            else:
                # Choose the better section based on multiple criteria
                current = sections_by_type[section_type]
                new = boundary
                
                # Prefer sections with more content
                content_score_current = len(current.content.strip())
                content_score_new = len(new.content.strip())
                
                # Prefer sections that appear later (more likely to be the actual content)
                position_score_current = current.start_line
                position_score_new = new.start_line
                
                # For skills specifically, prefer sections with bullet points or commas
                if section_type == 'skills':
                    skills_indicators_current = sum(1 for char in ['•', '▪', '-', ',', ';'] if char in current.content)
                    skills_indicators_new = sum(1 for char in ['•', '▪', '-', ',', ';'] if char in new.content)
                    
                    if skills_indicators_new > skills_indicators_current:
                        sections_by_type[section_type] = new
                    elif skills_indicators_new == skills_indicators_current and content_score_new > content_score_current:
                        sections_by_type[section_type] = new
                else:
                    # For other sections, prefer later position if confidence is similar
                    if (new.detection_confidence >= current.detection_confidence * 0.9 and 
                        (content_score_new > content_score_current or position_score_new > position_score_current)):
                        sections_by_type[section_type] = new
                    elif new.detection_confidence > current.detection_confidence:
                        sections_by_type[section_type] = new
        
        # Step 3: Extract personal info
        if personal_info:
            try:
                first_name = str(personal_info.first_name or '')
                last_name = str(personal_info.last_name or '')
                
                if hasattr(personal_info, 'phone_number'):
                    phone = str(personal_info.phone_number or '')
                elif hasattr(personal_info, 'phone'):
                    phone = str(personal_info.phone or '')
                else:
                    phone = ''
                    
                address = str(personal_info.address or '')
                
                if hasattr(personal_info, 'date_of_birth'):
                    date_of_birth = str(personal_info.date_of_birth or '')
                else:
                    date_of_birth = ''
                    
            except AttributeError:
                first_name, last_name, phone, address = extractor.extract_contact_info(text)
                date_of_birth = ""
        else:
            first_name, last_name, phone, address = extractor.extract_contact_info(text)
            date_of_birth = ""
        
        # Step 4: Extract content from detected sections
        summary = extractor.extract_summary(sections_by_type.get('summary'))
        skills = extractor.extract_skills(sections_by_type.get('skills'))
        experience = extractor.extract_experience(sections_by_type.get('experience'))
        education = extractor.extract_education(sections_by_type.get('education'))
        
        return CVSummary(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            date_of_birth=date_of_birth,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education
        )

# Backward compatibility
CVExtractor = DynamicCVExtractor