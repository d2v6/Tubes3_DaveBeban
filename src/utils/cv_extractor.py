import re
from datetime import datetime
import os
import json
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
    experience: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)

class RegexExtractor:
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:(?:\+?\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2,3}\d{3,4}',
            'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
            'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
            'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|BBA|A\.A\.|Associates?|Diploma|Certificate|High School Diploma)\b',
            'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
        }
        self.debug_mode = False 
        self.current_filename = ""

    def save_debug(self, step, content):
        if self.debug_mode:
            debug_dir = "debug_regex_extraction"
            os.makedirs(debug_dir, exist_ok=True)
            
            filename_base = self.current_filename if self.current_filename else "unknown_cv"
            filename = f"{filename_base}_{step}.txt"
            filepath = os.path.join(debug_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
            except Exception as e:
                print(f"Error saving debug file {filepath}: {e}")

    def extract_personal_info(self, text):
        info = {}
        try:
            text_start = text[:1000]
            
            email_match = re.search(self.patterns['email'], text)
            if email_match:
                info['email'] = email_match.group(0)
            
            phone_patterns = [
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\+1\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text_start)
                if phone_match:
                    info['phone'] = phone_match.group(0).strip()
                    break
            
            lines = text.split('\n')
            for i, line in enumerate(lines[:5]):
                line = line.strip()
                if not line: continue
                if any(header in line.upper() for header in ['SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE', 'EDUCATION', 'PROFILE']):
                    continue
                if len(line) < 50:
                    if line.isupper() and ' ' in line and len(line.split()) > 1 and len(line.split()) < 4 :
                        is_likely_name = True
                        for word in line.split():
                            if word in ['ACCOUNTANT', 'MANAGER', 'ENGINEER', 'DEVELOPER', 'ANALYST', 'ADVOCATE', 'SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE', 'PROFILE']:
                                is_likely_name = False
                                break
                        if is_likely_name:
                            info['name'] = line.title()
                            break
                    elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$', line):
                        info['name'] = line
                        break
        except Exception as e:
            print(f"Error in extract_personal_info: {str(e)}")
        return info

    def extract_summary(self, text):
        summary = ""
        try:
            summary_patterns = [
                r'Summary\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)',
                r'Objective\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)',
                r'Profile\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)'
            ]
            
            for pattern in summary_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    summary_text = match.group(1).strip()
                    summary_text = re.sub(r'\s+', ' ', summary_text)
                    if 20 < len(summary_text) < 1000:
                        summary = summary_text[:500]
                        return summary
        except Exception as e:
            print(f"Error in extract_summary: {str(e)}")
        return summary

    def extract_skills(self, text):
        skills = []
        try:
            skills_section_patterns = [
                r'Skills\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations|Interests|Awards)|$)',
                r'Technical Skills\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations)|$)',
                r'Core Competencies\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations)|$)',
                r'Highlights\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Accomplishments)|$)'
            ]
            
            skills_text_content = ""
            for pattern in skills_section_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    skills_text_content = match.group(1).strip()
                    break
            
            temp_skills_list = []
            if skills_text_content:
                lines = skills_text_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    line = re.sub(r'^[•\-*]\s*', '', line)
                    
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            skill_list_after_colon = parts[1]
                            sub_skills_from_colon = re.split(r'[,;]', skill_list_after_colon)
                            for skill_item in sub_skills_from_colon:
                                skill_item = skill_item.strip().rstrip('.')
                                if 2 < len(skill_item) < 50 and skill_item:
                                    temp_skills_list.append(skill_item)
                    else:
                        if ';' in line or (',' in line and line.count(',') > 0 and line.count(',') < 5) :
                            sub_skills_from_line = re.split(r'[,;]', line)
                            for skill_item in sub_skills_from_line:
                                skill_item = skill_item.strip().rstrip('.')
                                if 2 < len(skill_item) < 50 and skill_item:
                                    temp_skills_list.append(skill_item)
                        elif 2 < len(line) < 100 and not any(header in line.upper() for header in ['EXPERIENCE', 'EDUCATION', 'CERTIFICATIONS']):
                            temp_skills_list.append(line.rstrip('.'))

            tech_skills_found = set()
            tech_pattern = r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Swift|Kotlin|Go|R\b|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|Oracle|HTML5?|CSS3?|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|Docker|Kubernetes|AWS|Azure|GCP|Git|Machine Learning|Data Analysis|Data Science|AI|DevOps|Linux|Windows|Excel|Word|PowerPoint|Outlook|QuickBooks|Accounting|General Accounting|Accounts Payable|Payroll|Financial Analysis|Financial Reporting|Budget(?:ing)?|Audit(?:ing)?|Tax(?:ation)?|GAAP|SAP|ERP|Program Management|Project Management|Customer Service|Communication|Leadership|Teamwork|Problem Solving|Microsoft Office|CPA)\b'
            tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)
            for tech in tech_matches:
                tech_skills_found.add(tech)
            
            temp_skills_list.extend(list(tech_skills_found))
            
            seen = set()
            unique_skills = []
            for skill_val in temp_skills_list:
                skill_lower = skill_val.lower().strip()
                if skill_lower not in seen and skill_lower:
                    seen.add(skill_lower)
                    unique_skills.append(skill_val)
            
            skills = unique_skills
        except Exception as e:
            print(f"Error in extract_skills: {str(e)}")
        return skills[:20]

    def extract_experience(self, text):
        experience = []
        exp_text = ""
        try:
            # normalisasi karakter yang goofy ahh
            text = text.replace('â€"', '-').replace('â€"', '-').replace('\u2013', '-')
            
            # More flexible experience section detection
            exp_section_patterns = [    
                r'Accomplishments\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)',
                r'Work Experience[s]?\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)',
                r'Work History\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)',
                r'Experience\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)',
                r'Professional Experience[s]?\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)'
            ]
            
            for pattern in exp_section_patterns:
                exp_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if exp_match:
                    exp_text = exp_match.group(1).strip()
                    break

            if not exp_text:
                return []

            # Improved job patterns
            pattern_construction_mm_yyyy = r'([A-Za-z\s\/]+?)\s+(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n+Company\s*Name\s*[^\w]*([^\n]+)'
            pattern_original_mm_yyyy = r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n+([^\n]+?)\s+Company\s*Name\s*:\s*([^\n]+)'
            pattern_pos_company_loc = r'([A-Za-z\s,/-]+?)\s+Company\s*Name\s*[^\w]*([^\n]+)'
            pattern_accountant_job = r'^(Company Name)\s*\n+([A-Za-z]+\s+\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|Current|Present)\s*\n+([^\n]+?)\s*\n+([^\n]*(?:City|State)[^\n]*)\s*\n+'
            pattern_bullet_format = r'^([A-Za-z\s]+)\n(\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{4}|Present)\n([^\n]+)\n([^\n]+)'

            job_patterns = [
                pattern_construction_mm_yyyy,
                pattern_bullet_format,
                pattern_original_mm_yyyy,
                pattern_accountant_job,
                pattern_pos_company_loc
            ]

            all_exp_matches = []
            matched_pattern_type = None
            
            for idx, pattern_str in enumerate(job_patterns):
                flags = re.IGNORECASE | re.DOTALL
                if pattern_str.startswith('^'):
                    flags |= re.MULTILINE
                current_matches = list(re.finditer(pattern_str, exp_text, flags))
                if current_matches:
                    all_exp_matches = current_matches
                    if pattern_str == pattern_construction_mm_yyyy: 
                        matched_pattern_type = "construction_mm_yyyy"
                    elif pattern_str == pattern_original_mm_yyyy: 
                        matched_pattern_type = "original_mm_yyyy"
                    elif pattern_str == pattern_accountant_job: 
                        matched_pattern_type = "accountant_month_yyyy"
                    elif pattern_str == pattern_pos_company_loc: 
                        matched_pattern_type = "pos_company_loc"
                    elif pattern_str == pattern_bullet_format:
                        matched_pattern_type = "bullet_format"
                    break 
            
            if all_exp_matches:
                for i, match_obj in enumerate(all_exp_matches):
                    exp_entry = ""
                    company = ""
                    position = ""
                    start_date = ""
                    end_date = ""
                    location = ""

                    if matched_pattern_type == "construction_mm_yyyy":
                        position = match_obj.group(1).strip()
                        start_date = match_obj.group(2)
                        end_date = match_obj.group(3)
                        company = match_obj.group(4).strip() if match_obj.lastindex >= 4 else ""
                        exp_entry = f"{position} at {company}\n{start_date} - {end_date}"
                    
                    elif matched_pattern_type == "bullet_format":
                        position = match_obj.group(1).strip()
                        start_date = match_obj.group(2)
                        end_date = match_obj.group(3)
                        company = match_obj.group(4).strip()
                        location = match_obj.group(5).strip()
                        exp_entry = f"{position} at {company}, {location}\n{start_date} - {end_date}"
                    
                    elif matched_pattern_type == "original_mm_yyyy":
                        start_date = match_obj.group(1)
                        end_date = match_obj.group(2)
                        position = match_obj.group(3).strip()
                        company = match_obj.group(4).strip() if match_obj.lastindex >= 4 else ""
                        exp_entry = f"{position} at {company}\n{start_date} - {end_date}"
                    
                    elif matched_pattern_type == "accountant_month_yyyy":
                        company_placeholder = match_obj.group(1).strip()
                        start_date = match_obj.group(2).strip()
                        end_date = match_obj.group(3).strip()
                        position = match_obj.group(4).strip()
                        location = match_obj.group(5).strip()
                        company = location if company_placeholder.lower() == "company name" else company_placeholder
                        exp_entry = f"{position} at {company}\n{start_date} - {end_date}"

                    elif matched_pattern_type == "pos_company_loc":
                        position = match_obj.group(1).strip()
                        company = match_obj.group(2).strip() 
                        before_text = exp_text[:match_obj.start()]
                        date_pattern_exp = r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|Current|Present)'
                        date_match_exp = None
                        for dm_exp in reversed(list(re.finditer(date_pattern_exp, before_text))):
                            date_match_exp = dm_exp
                            break
                        if date_match_exp:
                            start_date = date_match_exp.group(1)
                            end_date = date_match_exp.group(2)
                            exp_entry = f"{position} at {company}\n{start_date} - {end_date}"
                        else:
                            exp_entry = f"{position} at {company}"
                    
                    if exp_entry:
                        start_pos_resp = match_obj.end()
                        end_pos_resp = len(exp_text)
                        if i + 1 < len(all_exp_matches):
                            end_pos_resp = all_exp_matches[i+1].start()
                        
                        resp_text_segment = exp_text[start_pos_resp:end_pos_resp].strip()
                        responsibilities_list = []
                        resp_lines = resp_text_segment.split('\n')
                        for resp_line in resp_lines:
                            resp_line = resp_line.strip()
                            resp_line = re.sub(r'^[•*-]\s*', '', resp_line)
                            if resp_line and len(resp_line) > 10 and \
                            not re.match(r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to', resp_line) and \
                            not resp_line.lower().startswith("company name"):
                                responsibilities_list.append(f"• {resp_line}")
                                if len(responsibilities_list) >= 2:
                                    break
                        if responsibilities_list:
                            exp_entry += "\n" + "\n".join(responsibilities_list)
                        experience.append(exp_entry)
                    if len(experience) >= 5: 
                        break
        except Exception as e:
            print(f"Error in extract_experience: {str(e)}")
        return experience[:5]

    def extract_education(self, text):
        education = []
        edu_text = ""
        try:
            # Normalize special characters
            text = text.replace('â€"', '-').replace('â€"', '-').replace('\u2013', '-')
            
            # More flexible education section detection
            edu_patterns_main = [
                r'Education(?:\s+and\s+Training)?\s*\n+(.*?)(?=\n(?:Skills|Professional Affiliations|Certifications|Interests|Additional Information|Awards|Languages)|$)',
                r'Education\s*\n+(.*?)(?=\n(?:Experience|Work History|Employment History)|$)',
                r'Education\s*\n+(.*?)$'
            ]
            
            for pattern in edu_patterns_main:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    edu_text = match.group(1).strip()
                    break
            
            if edu_text:
                pattern_edu_kentucky = r'^(\d{4})\s*\n+([A-Z]\.[A-Z]\.)\s*:\s*([^\n]+?)\s*(?:1/4|\||-)\s*([^\n]+(?:University|College|Institute|School)[^\n]*)'
                pattern_edu_certificate = r'Certificate\s*(?:of\s*Completion)?\s*:\s*([^\n]+?)\s*(\d{4})\s*([^\n]+)'
                pattern_edu_aa_field_year = r'([A-Z]\.[A-Z]\.|Bachelor|Master|MBA|BBA|PhD|Diploma|Certificate)\s*:\s*([^,\n]+?)(?:\s*,\s*(\d{4}))?'
                pattern_edu_month_year_degree_fieldinst = r'([A-Za-z]+\s+\d{4})\s+([^:]+)\s*:\s*([^\n]+)'
                pattern_edu_degree_of_field_inst = r'(Bachelor|Master|MBA|BBA|PhD)\s+(?:of\s+)?([^,\n]+?)(?:\s+(?:from|at)\s+)?([A-Z][^\n]*(?:University|College|Institute|School))'
                pattern_edu_consumer_advocate = r'^(Certificate[^\n]*\.\s*)\n+([A-Z][A-Za-z\s.,&-]+(?:Association|Institute|School|College|University))\s*(?:\n*:\s*\n*([A-Za-z\s]+,\s*[A-Z]{2}))?'
                pattern_edu_accountant = r'^([A-Z][A-Za-z\s.,-]+(?:University|College|Institute|School))\s*\n+(\d{4})\s*\n+([A-Za-z.\s()]+?)\s*:\s*([^,\n]+)'

                degree_patterns_list = [
                    pattern_edu_kentucky,  # ADDED FIRST TO GIVE IT PRIORITY
                    pattern_edu_certificate,
                    pattern_edu_aa_field_year,
                    pattern_edu_month_year_degree_fieldinst,
                    pattern_edu_degree_of_field_inst,
                    pattern_edu_consumer_advocate,
                    pattern_edu_accountant
                ]
                
                for pattern_str in degree_patterns_list:
                    flags = re.IGNORECASE | re.DOTALL | re.MULTILINE  # Added MULTILINE flag
                    
                    matches = list(re.finditer(pattern_str, edu_text, flags))
                    
                    if matches:
                        for match_obj in matches:
                            groups = match_obj.groups()
                            edu_entry = ""
                            year = ""

                            # Handle the Kentucky-specific format
                            if pattern_str == pattern_edu_kentucky:
                                year = groups[0]
                                degree = groups[1]
                                field = groups[2].strip()
                                institution = groups[3].strip()
                                edu_entry = f"{degree} in {field} - {institution} ({year})"
                            
                            # Handle certificate format
                            elif pattern_str == pattern_edu_certificate:
                                program = groups[0].strip()
                                year = groups[1]
                                institution = groups[2].strip()
                                edu_entry = f"Certificate in {program} - {institution} ({year})"
                            
                            elif pattern_str == pattern_edu_aa_field_year:
                                degree = groups[0]
                                field = groups[1].strip()
                                year = groups[2] if len(groups) > 2 and groups[2] else ""
                                after_text = edu_text[match_obj.end():match_obj.end()+200]
                                inst_match_edu = re.search(r'([A-Z][^\n:,]+(?:University|College|Institute|School))', after_text)
                                institution = inst_match_edu.group(1).strip() if inst_match_edu else ""
                                if institution: 
                                    edu_entry = f"{degree} in {field} - {institution}"
                                else: 
                                    edu_entry = f"{degree} in {field}"
                                if year: 
                                    edu_entry += f" ({year})"
                            
                            elif pattern_str == pattern_edu_month_year_degree_fieldinst:
                                date = groups[0]
                                year = re.search(r'\d{4}', date).group(0) if re.search(r'\d{4}', date) else ""
                                degree_text = groups[1].strip()
                                field_and_inst = groups[2].strip()
                                inst_match_edu = re.search(r'([A-Z][^\n]+(?:University|College|Institute|School))', field_and_inst)
                                if inst_match_edu:
                                    institution = inst_match_edu.group(1).strip()
                                    field = field_and_inst.replace(institution, '').strip()
                                    edu_entry = f"{degree_text} in {field} - {institution} ({date})"
                                else:
                                    edu_entry = f"{degree_text} in {field_and_inst} ({date})"
                            
                            elif pattern_str == pattern_edu_degree_of_field_inst:
                                degree = groups[0].strip()
                                field = groups[1].strip()
                                institution = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                                edu_entry = f"{degree} in {field}"
                                if institution: 
                                    edu_entry += f" - {institution}"
                                context_around_match = edu_text[max(0, match_obj.start()-50) : min(len(edu_text), match_obj.end()+50)]
                                year_match_edu = re.search(r'\b((?:19|20)\d{2})\b', context_around_match)
                                if year_match_edu and not year in edu_entry:
                                    edu_entry += f" ({year_match_edu.group(1)})"
                                    year = year_match_edu.group(1)
                            
                            elif pattern_str == pattern_edu_consumer_advocate:
                                description = groups[0].strip()
                                institution = groups[1].strip()
                                location = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                                edu_entry = f"{description} - {institution}"
                                if location: 
                                    edu_entry += f" ({location})"
                            
                            elif pattern_str == pattern_edu_accountant:
                                institution = groups[0].strip()
                                year = groups[1].strip()
                                degree = groups[2].strip()
                                field = groups[3].strip()
                                edu_entry = f"{degree} in {field} - {institution} ({year})"
                            if edu_entry and edu_entry not in education:
                                education.append(edu_entry)
                            if len(education) >= 3: 
                                break
                        if education: 
                            break
                
                # Fallback for very unusual formats
                if not education:
                    edu_lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
                    if len(edu_lines) >= 2:
                        education.append("\n".join(edu_lines[:3]))
        except Exception as e:
            print(f"Error in extract_education: {str(e)}")
        return education[:3]

    def extract_all(self, text):
        try:
            if hasattr(self, '_current_cv_path_for_debug'):
                self.current_filename = os.path.basename(self._current_cv_path_for_debug).replace('.pdf', '')
            elif 'unknown' not in self.current_filename and self.current_filename :
                 pass
            else:
                first_line = text.split('\n')[0].strip()
                potential_name = "".join(c for c in first_line if c.isalnum() or c == ' ')[:30].replace(" ","_")
                self.current_filename = potential_name if potential_name else "unknown_cv"

            
            if len(text) > 70000:
                text = text[:70000]
            
            result = {
                'personal_info': self.extract_personal_info(text),
                'summary': self.extract_summary(text),
                'skills': self.extract_skills(text),
                'experience': self.extract_experience(text),
                'education': self.extract_education(text)
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error in extract_all: {str(e)}"
            print(f"Error in extract_all: {str(e)}")            
            return {
                'personal_info': {}, 'summary': '', 'skills': [],
                'experience': [], 'education': []
            }

class DynamicCVExtractor:
    """Wrapper class for backward compatibility using RegexExtractor"""
    
    def __init__(self):
        self.regex_extractor = RegexExtractor()
    
    @staticmethod
    def extract_full_summary(text: str, personal_info=None) -> CVSummary:
        """Static method for compatibility with existing code using enhanced extraction"""
        extractor = RegexExtractor()
        extracted_data = extractor.extract_all(text)
        
        # Handle personal info
        personal = extracted_data.get('personal_info', {})
        name_parts = personal.get('name', '').split() if personal.get('name') else []
        
        return CVSummary(
            first_name=name_parts[0] if name_parts else "",
            last_name=" ".join(name_parts[1:]) if len(name_parts) > 1 else "",
            phone=personal.get('phone', ''),
            summary=extracted_data.get('summary', ''),
            skills=extracted_data.get('skills', []),
            experience=extracted_data.get('experience', []),
            education=extracted_data.get('education', [])
        )
    
    def detect_all_sections(self, cv_text: str) -> List[SectionBoundary]:
        """Detect all sections for backward compatibility"""
        extracted_data = self.regex_extractor.extract_all(cv_text)
        
        sections = []
        current_line = 0
        
        for section_type, content in extracted_data.items():
            if content and section_type in ['summary', 'skills', 'experience', 'education']:
                if isinstance(content, str):
                    content_str = content
                elif isinstance(content, list):
                    content_str = '\n'.join(content)
                else:
                    content_str = str(content)
                
                sections.append(SectionBoundary(
                    section_type=section_type,
                    start_line=current_line,
                    end_line=current_line + len(content_str.split('\n')),
                    content=content_str,
                    detection_confidence=0.9
                ))
                current_line += len(content_str.split('\n')) + 1
        
        return sections
    
    def extract_contact_info(self, cv_text: str) -> Dict[str, str]:
        """Extract contact information using regex patterns"""
        personal_info = self.regex_extractor.extract_personal_info(cv_text)
        
        # Extract name parts
        name = personal_info.get('name', '')
        name_parts = name.split() if name else []
        
        return {
            'first_name': name_parts[0] if name_parts else "",
            'last_name': " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
            'phone': personal_info.get('phone', ''),
            'email': personal_info.get('email', ''),
            'name': name
        }
    
    def extract_summary(self, cv_text: str) -> CVSummary:
        """Extract complete CV summary using regex extractor"""
        extracted_data = self.regex_extractor.extract_all(cv_text)
        contact_info = self.extract_contact_info(cv_text)
        
        return CVSummary(
            first_name=contact_info.get('first_name', ''),            last_name=contact_info.get('last_name', ''),
            phone=contact_info.get('phone', ''),
            summary=extracted_data.get('summary', ''),
            skills=extracted_data.get('skills', []),
            experience=extracted_data.get('experience', []),
            education=extracted_data.get('education', [])        )
# Backward compatibility
CVExtractor = DynamicCVExtractor