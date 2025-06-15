from src.database.connection import DatabaseConnection
from src.utils.pdf_parser import PDFParser
from src.utils.encryption import FieldEncryption
from src.models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
from src.algorithms.string_matcher_unified import StringMatcher
from src.algorithms.kmp_search import KMPSearch
from src.algorithms.boyer_moore_search import BoyerMooreSearch
from src.algorithms.levenshtein_distance import LevenshteinDistance
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class CVRepository:
    """🗂️ REPOSITORY: Clean data layer for CV ATS System"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.pdf_parser = PDFParser()
        self.string_matcher = StringMatcher()
        self.field_encryption = FieldEncryption()

        self.project_root = self._get_project_root()
        self.data_folder = os.path.join(self.project_root, "data")
        self.cvs_folder = os.path.join(self.data_folder, "cvs")

        self.loaded_cvs = []

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

    def connect(self) -> bool:
        """Connect to database"""
        return self.db.connect()

    def disconnect(self):
        """Disconnect from database"""
        self.db.disconnect()

    def is_connected(self) -> bool:
        """Check connection status"""
        return self.db.is_connected()

    def get_all_cvs(self) -> List[CVSearchResult]:
        """
        Get all CVs with profile data using multithreading or multiprocessing for faster PDF loading

        Returns:
            List of CVSearchResult objects
        """
        return self.get_all_cvs_multiprocessing()

    def get_statistics(self) -> Dict[str, Any]:
        """Get CV statistics"""
        try:
            query = """
            SELECT application_role, COUNT(*) as count_per_role
            FROM ApplicationDetail
            GROUP BY application_role
            ORDER BY count_per_role DESC
            """

            results = self.db.execute_query(query)

            if results:
                total_query = "SELECT COUNT(*) as total FROM ApplicationDetail"
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

    def search_cvs_by_keywords(self, keywords: str, algorithm: str = "kmp", top_matches: int = 10) -> List[CVSearchResult]:
        """🔍 SEARCH: Main search function using your algorithms"""
        try:
            print(f"Starting search with keywords: '{keywords}' using {algorithm.upper()}")

            if (not self.loaded_cvs):
                print("Loading CVs from database...")
                self.loaded_cvs = self.get_all_cvs()
            all_cvs = self.loaded_cvs
            if not all_cvs:
                print("❌ No CVs found in database!")
                return []

            print(f"Found {len(all_cvs)} CVs to search")

            keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
            if not keyword_list:
                print("❌ No valid keywords provided!")
                return []

            print(f"Searching for keywords: {keyword_list}")

            thresholds = {}
            for keyword in keyword_list:
                term_length = len(keyword)
                if term_length <= 3:
                    thresholds[keyword] = 1.0
                elif term_length <= 5:
                    thresholds[keyword] = 0.95
                elif term_length <= 8:
                    thresholds[keyword] = 0.85
                elif term_length <= 12:
                    thresholds[keyword] = 0.8
                else:
                    thresholds[keyword] = 0.7

            search_results = []
            search_times = {'exact': 0, 'fuzzy': 0}

            for i, cv_result in enumerate(all_cvs, 1):
                try:
                    if not cv_result.cv_text or len(cv_result.cv_text.strip()) < 10:
                        continue

                    matched_keywords = []
                    remaining_keywords = keyword_list.copy() 

                    if algorithm == "aho":
                        exact_start = time.time()
                        aho_results = self.string_matcher.aho_corasick_search(cv_result.cv_text, keyword_list)
                        search_times['exact'] += time.time() - exact_start
                        if aho_results:
                            keywords_found_by_aho = []
                            for keyword, positions in aho_results.items():
                                match_count = len(positions) if positions else 0
                                if match_count > 0:
                                    matched_keywords.append((keyword, match_count))
                                    keywords_found_by_aho.append(keyword)
                            remaining_keywords = [kw for kw in remaining_keywords if kw not in keywords_found_by_aho]

                    for keyword in remaining_keywords:
                        exact_start = time.time()
                        exact_matches = self._find_exact(cv_result.cv_text, keyword, algorithm)
                        search_times['exact'] += time.time() - exact_start

                        if exact_matches > 0:
                            matched_keywords.append((keyword, exact_matches))
                            # print(f"Exact match found for '{keyword}' in CV {i}: {exact_matches} occurrences")
                        else:
                            fuzzy_start = time.time()
                            fuzzy_matches = self._find_fuzzy(cv_result.cv_text, keyword, thresholds[keyword])
                            search_times['fuzzy'] += time.time() - fuzzy_start

                            if fuzzy_matches:
                                matched_keywords.extend(fuzzy_matches)
                                # print(f"Fuzzy match found for '{keyword}' in CV {i}: {len(fuzzy_matches)} occurrences")

                    if matched_keywords:
                        cv_result.matched_keywords = matched_keywords
                        search_results.append(cv_result)

                except Exception as e:
                    print(f"❌ Error processing CV {i}: {e}")
                    continue

            search_results.sort(key=lambda x: sum(count for _, count in x.matched_keywords), reverse=True)
            top_results = search_results[:top_matches]

            # print(f"Timing - Exact: {search_times['exact']:.3f}s, Fuzzy: {search_times['fuzzy']:.3f}s")

            for result in top_results:
                result.search_timing = search_times

            print(f"Found {len(top_results)} matching CVs")
            return top_results

        except Exception as e:
            print(f"❌ Error searching CVs: {e}")
            return []

    def _find_exact(self, cv_text: str, keyword: str, algorithm: str) -> int:
        try:
            cv_text_lower = cv_text.lower()
            keyword_lower = keyword.lower()

            if algorithm == "kmp":
                matches = self.string_matcher.kmp_search(
                    cv_text_lower, keyword_lower)
                return len(matches) if isinstance(matches, list) else matches
            elif algorithm == "bm":
                matches = self.string_matcher.boyer_moore_search(
                    cv_text_lower, keyword_lower)
                return len(matches) if isinstance(matches, list) else matches
            elif algorithm == "aho":
                return 0
            else:
                import re
                matches = len(re.findall(
                    re.escape(keyword_lower), cv_text_lower))
                return matches

        except Exception as e:
            print(f"⚠️ Error in exact match calculation: {e}")
            return 0


    def _find_fuzzy(self, cv_text: str, keyword: str, threshold: float = 0.95) -> List[tuple[str, int]]:
        """Find fuzzy matches of keyword in CV text and return list of (word, count) pairs"""
        try:
            keyword_counts = {}
            keyword_lower = keyword.lower()
            cv_text_lower = cv_text.lower()
            
            if ' ' in keyword_lower:
                keyword_words = keyword_lower.split()
                keyword_length = len(keyword_words)
                cv_words = cv_text_lower.split()
                
                for i in range(len(cv_words) - keyword_length + 1):
                    window = ' '.join(cv_words[i:i + keyword_length])
                    
                    similarity = self.string_matcher.calculate_similarity(
                        keyword_lower, window) / 100
                    
                    if similarity >= threshold:
                        if window in keyword_counts:
                            keyword_counts[window] += 1
                        else:
                            keyword_counts[window] = 1
            else:
                cv_words = cv_text_lower.split()
                
                for word in cv_words:
                    similarity = self.string_matcher.calculate_similarity(
                        keyword_lower, word) / 100
                    
                    if similarity >= threshold:
                        if word in keyword_counts:
                            keyword_counts[word] += 1
                        else:
                            keyword_counts[word] = 1
            
            matched_keywords = [(word, count) for word, count in keyword_counts.items()]
            return matched_keywords
            
        except Exception as e:
            print(f"⚠️ Error in fuzzy match calculation: {e}")
            return []

    def get_cv_summary_statistics(self) -> Dict[str, Any]:
        """Get CV summary statistics"""
        try:
            total_query = "SELECT COUNT(*) as total FROM ApplicationDetail"
            total_result = self.db.execute_query(total_query)
            total_cvs = total_result[0]['total'] if total_result else 0
            role_query = """
            SELECT application_role, COUNT(*) as count_per_role
            FROM ApplicationDetail
            GROUP BY application_role
            ORDER BY count_per_role DESC
            """

            role_results = self.db.execute_query(role_query)
            role_breakdown = {row['application_role']: row['count_per_role']
                              for row in role_results} if role_results else {}

            return {
                'total_cvs': total_cvs,
                'total_roles': len(role_breakdown),
                'role_breakdown': role_breakdown
            }

        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {'total_cvs': 0, 'total_roles': 0, 'role_breakdown': {}}

    def get_all_cvs_multiprocessing(self) -> List[CVSearchResult]:
        try:
            from concurrent.futures import ProcessPoolExecutor
            import multiprocessing as mp

            query = """
            SELECT 
                ap.applicant_id, ap.first_name, ap.last_name, ap.date_of_birth,
                ap.address, ap.phone_number,
                ad.detail_id, ad.application_role, ad.cv_path
            FROM ApplicantProfile ap
            JOIN ApplicationDetail ad ON ap.applicant_id = ad.applicant_id
            """

            results = self.db.execute_query(query)
            cv_results = []

            if results:
                print(f"🔄 Loading {len(results)} CVs using multiprocessing...")
                start_time = time.time()

                cv_tasks = []
                for row in results:
                    try:
                        decrypted_row = self.field_encryption.decrypt_profile_data(row)
                        
                        cv_tasks.append({
                            'applicant_id': decrypted_row['applicant_id'],
                            'first_name': decrypted_row['first_name'],
                            'last_name': decrypted_row['last_name'],
                            'date_of_birth': decrypted_row['date_of_birth'],
                            'address': decrypted_row['address'],
                            'phone_number': decrypted_row['phone_number'],
                            'detail_id': row['detail_id'],
                            'application_role': row['application_role'],
                            'cv_path': row['cv_path']
                        })
                    except Exception as e:
                        print(f"⚠️ Error preparing CV data: {e}")
                        continue

                max_workers = min(mp.cpu_count(), len(cv_tasks))

                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(
                        self._process_single_cv, task) for task in cv_tasks]

                    completed_count = 0
                    for future in as_completed(futures):
                        try:
                            cv_result = future.result()
                            if cv_result:
                                cv_results.append(cv_result)
                            completed_count += 1

                            if completed_count % 50 == 0 or completed_count == len(cv_tasks):
                                print(
                                    f"📁 Processed {completed_count}/{len(cv_tasks)} CVs...")

                        except Exception as e:
                            print(f"⚠️ Error in multiprocessing: {e}")
                            continue

                end_time = time.time()
                processing_time = end_time - start_time
                print(
                    f"✅ Loaded {len(cv_results)} CVs in {processing_time:.2f} seconds (multiprocessing)")
                print(
                    f"Average: {processing_time/len(cv_results):.3f}s per CV")

            self.loaded_cvs = cv_results
            return cv_results

        except Exception as e:
            print(f"❌ Error retrieving CVs with multiprocessing: {e}")
            return []

    @staticmethod
    def _process_single_cv(task_data: Dict[str, Any]) -> Optional[CVSearchResult]:
        """
        Static method for multiprocessing CV loading
        Must be static to be picklable for multiprocessing
        """
        try:
            from utils.pdf_parser import PDFParser
            from models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
            from pathlib import Path

            profile = ApplicantProfile(
                applicant_id=task_data['applicant_id'],
                first_name=task_data['first_name'],
                last_name=task_data['last_name'],
                date_of_birth=task_data['date_of_birth'],
                address=task_data['address'],
                phone_number=task_data['phone_number'],
            )

            application = ApplicationDetail(
                detail_id=task_data['detail_id'],
                applicant_id=task_data['applicant_id'],
                application_role=task_data['application_role'],
                cv_path=task_data['cv_path'],
                applicant_profile=profile
            )

            pdf_parser = PDFParser()

            cv_path = task_data['cv_path']
            clean_path = cv_path.strip('/\\')
            project_root = Path(__file__).parent.parent.parent
            file_path = str(project_root / clean_path)

            if not os.path.exists(file_path):
                return None

            cv_text = pdf_parser.parse_pdf(file_path)

            if cv_text is None:
                return None

            cv_result = CVSearchResult(
                applicant_profile=profile,
                application_detail=application,
                cv_text=cv_text
            )

            return cv_result

        except Exception as e:
            print(f"Error in process loading CV: {e}")
            return None

    def get_cv_by_index(self, index: int) -> Optional[CVSearchResult]:
        """Get CV by index from loaded CVs"""
        if 0 <= index < len(self.loaded_cvs):
            return self.loaded_cvs[index]
        return None
