from typing import List, Optional, Dict, Any
from .connection import DatabaseConnection

# Import models
try:
    from ..models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
except ImportError:
    from models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult

# Import utilities
try:
    from ..utils.pdf_parser import PDFParser
    from ..algorithms.string_matcher import StringMatcher
except ImportError:
    from utils.pdf_parser import PDFParser
    from algorithms.string_matcher import StringMatcher

import os
import time


class CVRepository:
    """🗂️ REPOSITORY: Clean data layer for CV ATS System"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.pdf_parser = PDFParser()
        self.string_matcher = StringMatcher()

        # Project paths
        self.project_root = self._get_project_root()
        self.data_folder = os.path.join(self.project_root, "data")
        self.cvs_folder = os.path.join(self.data_folder, "cvs")

    def _get_project_root(self) -> str:
        """🔍 Find project root directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))

        while current_dir != os.path.dirname(current_dir):
            data_path = os.path.join(current_dir, 'data', 'cvs')
            if os.path.exists(data_path):
                return current_dir
            current_dir = os.path.dirname(current_dir)

        src_parent = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        return src_parent

    # =============================================================================
    # 🔌 CONNECTION MANAGEMENT
    # =============================================================================

    def connect(self) -> bool:
        """Connect to database"""
        return self.db.connect()

    def disconnect(self):
        """Disconnect from database"""
        self.db.disconnect()

    def is_connected(self) -> bool:
        """Check connection status"""
        return self.db.is_connected()

    # =============================================================================
    # 📊 BASIC DATABASE OPERATIONS
    # =============================================================================

    def get_all_cvs(self) -> List[CVSearchResult]:
        """Get all CVs with profile data"""
        try:
            query = """
            SELECT 
                ap.applicant_id, ap.first_name, ap.last_name, ap.date_of_birth,
                ap.address, ap.phone_number, ap.email, ap.created_at as profile_created,
                ad.detail_id, ad.application_role, ad.cv_path, ad.applied_date, ad.status
            FROM ApplicantProfile ap
            JOIN ApplicationDetail ad ON ap.applicant_id = ad.applicant_id
            WHERE ad.status = 'active'
            ORDER BY ad.applied_date DESC
            """

            results = self.db.execute_query(query)
            cv_results = []

            if results:
                for row in results:
                    try:
                        profile = ApplicantProfile(
                            applicant_id=row['applicant_id'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            date_of_birth=row['date_of_birth'],
                            address=row['address'],
                            phone_number=row['phone_number'],
                            email=row['email'],
                            created_at=row['profile_created']
                        )

                        application = ApplicationDetail(
                            detail_id=row['detail_id'],
                            applicant_id=row['applicant_id'],
                            application_role=row['application_role'],
                            cv_path=row['cv_path'],
                            applied_date=row['applied_date'],
                            status=row['status'],
                            applicant_profile=profile
                        )

                        # Load CV text from PDF
                        cv_text = self._load_cv_text(row['cv_path'])

                        cv_result = CVSearchResult(
                            applicant_profile=profile,
                            application_detail=application,
                            cv_text=cv_text
                        )

                        cv_results.append(cv_result)

                    except Exception as e:
                        print(f"⚠️ Error loading CV: {e}")
                        continue

            return cv_results

        except Exception as e:
            print(f"❌ Error retrieving CVs: {e}")
            return []

    def _load_cv_text(self, cv_path: str) -> str:
        """Load CV text from PDF file"""
        if not cv_path:
            return ""

        try:
            full_path = os.path.join(self.project_root, cv_path)

            if os.path.exists(full_path):
                cv_text = self.pdf_parser.parse_pdf(full_path)
                return cv_text if cv_text else ""
            else:
                print(f"⚠️ CV file not found: {full_path}")
                return ""

        except Exception as e:
            print(f"⚠️ Error loading CV text: {e}")
            return ""

    def get_statistics(self) -> Dict[str, Any]:
        """Get CV statistics"""
        try:
            query = """
            SELECT application_role, COUNT(*) as count_per_role
            FROM ApplicationDetail 
            WHERE status = 'active'
            GROUP BY application_role
            ORDER BY count_per_role DESC
            """

            results = self.db.execute_query(query)

            if results:
                total_query = "SELECT COUNT(*) as total FROM ApplicationDetail WHERE status = 'active'"
                total_result = self.db.execute_query(total_query)
                total_cvs = total_result[0]['total'] if total_result else 0

                return {
                    'total_cvs': total_cvs,
                    'total_roles': len(results),
                    'role_breakdown': {row['application_role']: row['count_per_role'] for row in results}
                }

            return {'total_cvs': 0, 'total_roles': 0, 'role_breakdown': {}}

        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {'total_cvs': 0, 'total_roles': 0, 'role_breakdown': {}}

    # =============================================================================
    # 🔍 SEARCH FUNCTIONS USING YOUR ALGORITHMS
    # =============================================================================

    def search_cvs_by_keywords(self, keywords: str, algorithm: str = "kmp", top_matches: int = 10, similarity_threshold: float = 0.3) -> List[CVSearchResult]:
        """🔍 SEARCH: Main search function using your algorithms"""
        try:
            print(f"🔍 Starting search with keywords: '{keywords}' using {algorithm.upper()}")
            
            # Get all CVs
            all_cvs = self.get_all_cvs()
            if not all_cvs:
                print("❌ No CVs found in database!")
                return []
            
            print(f"📁 Found {len(all_cvs)} CVs to search")
            
            # Prepare keywords (simple split for now)
            keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
            if not keyword_list:
                print("❌ No valid keywords provided!")
                return []
            
            print(f"🔎 Searching for keywords: {keyword_list}")
            
            # Search results with timing
            search_results = []
            search_times = {'exact': 0, 'fuzzy': 0}
            
            for i, cv_result in enumerate(all_cvs, 1):
                try:
                    if not cv_result.cv_text or len(cv_result.cv_text.strip()) < 10:
                        continue
                    
                    # Exact match phase
                    exact_start = time.time()
                    exact_score, exact_matches = self._calculate_exact_match_score(
                        cv_result.cv_text, keyword_list, algorithm
                    )
                    search_times['exact'] += time.time() - exact_start
                    
                    # If exact match is good enough, use it
                    if exact_score >= similarity_threshold:
                        cv_result.similarity_score = exact_score
                        cv_result.matched_keywords = exact_matches
                        cv_result.match_type = "exact"
                        search_results.append(cv_result)
                        print(f"✅ EXACT {i}: {cv_result.applicant_profile.full_name} - Score: {exact_score:.3f}")
                        continue
                    
                    # Fuzzy match phase (using your Levenshtein)
                    fuzzy_start = time.time()
                    fuzzy_score, fuzzy_matches = self._calculate_fuzzy_match_score(
                        cv_result.cv_text, keyword_list, 0.7  # 70% similarity threshold
                    )
                    search_times['fuzzy'] += time.time() - fuzzy_start
                    
                    if fuzzy_score >= similarity_threshold:
                        cv_result.similarity_score = fuzzy_score
                        cv_result.matched_keywords = fuzzy_matches
                        cv_result.match_type = "fuzzy"
                        search_results.append(cv_result)
                        print(f"✅ FUZZY {i}: {cv_result.applicant_profile.full_name} - Score: {fuzzy_score:.3f}")
                    
                except Exception as e:
                    print(f"❌ Error processing CV {i}: {e}")
                    continue
            
            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Return top matches with timing info
            top_results = search_results[:top_matches]
            
            print(f"🎉 Search completed: {len(top_results)} matches found")
            print(f"⏱️ Timing - Exact: {search_times['exact']:.3f}s, Fuzzy: {search_times['fuzzy']:.3f}s")
            
            # Store timing info for UI display
            for result in top_results:
                result.search_timing = search_times
            
            return top_results
            
        except Exception as e:
            print(f"❌ Error searching CVs: {e}")
            return []

    def _calculate_exact_match_score(self, cv_text: str, keywords: List[str], algorithm: str) -> tuple:
        """🧮 CALCULATE: Exact match score using your algorithms"""
        try:
            cv_text_lower = cv_text.lower()
            matched_keywords = []
            total_matches = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Use your algorithms
                if algorithm == "kmp":
                    matches = self.string_matcher.kmp_search(cv_text_lower, keyword_lower)
                elif algorithm == "bm":
                    matches = self.string_matcher.boyer_moore_search(cv_text_lower, keyword_lower)
                else:  # regex or fallback
                    import re
                    matches = len(re.findall(re.escape(keyword_lower), cv_text_lower))
                    matches = [0] if matches > 0 else []
                
                if matches:
                    matched_keywords.append(keyword)
                    total_matches += len(matches)
            
            # Calculate score
            if len(keywords) > 0:
                keyword_match_ratio = len(matched_keywords) / len(keywords)
                frequency_bonus = min(total_matches * 0.1, 1.0)
                score = keyword_match_ratio * 0.7 + frequency_bonus * 0.3
                return score, matched_keywords
            
            return 0.0, []
            
        except Exception as e:
            print(f"⚠️ Error in exact match calculation: {e}")
            return 0.0, []

    def _calculate_fuzzy_match_score(self, cv_text: str, keywords: List[str], threshold: float) -> tuple:
        """🧮 CALCULATE: Fuzzy match score using your Levenshtein algorithm"""
        try:
            cv_words = cv_text.lower().split()
            matched_keywords = []
            total_similarity = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                best_similarity = 0
                best_match = None
                
                # Find best fuzzy match using your Levenshtein
                for word in cv_words:
                    if len(word) >= 3:  # Only check words with 3+ chars
                        similarity = self.string_matcher.calculate_similarity(keyword_lower, word) / 100.0
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = word
                
                # If similarity is above threshold, count it
                if best_similarity >= threshold:
                    matched_keywords.append(f"{keyword}~{best_match}")
                    total_similarity += best_similarity
            
            # Calculate final score
            if len(keywords) > 0:
                keyword_match_ratio = len(matched_keywords) / len(keywords)
                avg_similarity = total_similarity / len(keywords) if matched_keywords else 0
                score = keyword_match_ratio * 0.6 + avg_similarity * 0.4
                return score, matched_keywords
            
            return 0.0, []
            
        except Exception as e:
            print(f"⚠️ Error in fuzzy match calculation: {e}")
            return 0.0, []

    # =============================================================================
    # 🎯 UTILITY METHODS
    # =============================================================================

    def test_algorithms(self, text: str, pattern: str) -> Dict[str, Any]:
        """🧪 TEST: Test your algorithms with sample data"""
        try:
            print(f"🧪 Testing algorithms with text length: {len(text)}, pattern: '{pattern}'")
            
            results = {}
            
            # Test KMP
            start_time = time.time()
            kmp_matches = self.string_matcher.kmp_search(text, pattern)
            kmp_time = time.time() - start_time
            results['kmp'] = {'matches': len(kmp_matches), 'time': kmp_time, 'positions': kmp_matches[:10]}
            
            # Test Boyer-Moore
            start_time = time.time()
            bm_matches = self.string_matcher.boyer_moore_search(text, pattern)
            bm_time = time.time() - start_time
            results['bm'] = {'matches': len(bm_matches), 'time': bm_time, 'positions': bm_matches[:10]}
            
            # Test Levenshtein (with sample words)
            words = text.split()[:100]  # First 100 words
            similarities = []
            start_time = time.time()
            for word in words:
                if len(word) >= 3:
                    sim = self.string_matcher.calculate_similarity(pattern, word)
                    if sim > 70:  # Only high similarities
                        similarities.append((word, sim))
            levenshtein_time = time.time() - start_time
            
            results['levenshtein'] = {
                'high_similarities': len(similarities),
                'time': levenshtein_time,
                'top_matches': sorted(similarities, key=lambda x: x[1], reverse=True)[:5]
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error testing algorithms: {e}")
            return {}