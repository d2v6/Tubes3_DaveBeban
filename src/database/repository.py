from algorithms.string_matcher import StringMatcher
from models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
from utils.pdf_parser import PDFParser
from pathlib import Path
from typing import List, Dict, Any, Optional
from .connection import DatabaseConnection
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import normally


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

        self.loaded_cvs = []  # Cache for loaded CVs

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

    def search_cvs_by_keywords(self, keywords: str, algorithm: str = "kmp", top_matches: int = 10, similarity_threshold: float = 0.3) -> List[CVSearchResult]:
        """🔍 SEARCH: Main search function using your algorithms"""
        try:
            print(
                f"Starting search with keywords: '{keywords}' using {algorithm.upper()}")

            # Get all CVs
            if (not self.loaded_cvs):
                print("Loading CVs from database...")
                self.loaded_cvs = self.get_all_cvs()
            all_cvs = self.loaded_cvs
            if not all_cvs:
                print("❌ No CVs found in database!")
                return []

            print(f"Found {len(all_cvs)} CVs to search")

            # Prepare keywords (simple split for now)
            keyword_list = [kw.strip().lower()
                            for kw in keywords.split(',') if kw.strip()]
            if not keyword_list:
                print("❌ No valid keywords provided!")
                return []

            print(f"Searching for keywords: {keyword_list}")

            # Search results with timing
            search_results = []
            search_times = {'exact': 0, 'fuzzy': 0}

            for i, cv_result in enumerate(all_cvs, 1):
                try:
                    if not cv_result.cv_text or len(cv_result.cv_text.strip()) < 10:
                        continue

                    # Exact match phase
                    exact_start = time.time()
                    exact_score, exact_matches, number_of_matches = self._calculate_exact_match_score(
                        cv_result.cv_text, keyword_list, algorithm
                    )
                    search_times['exact'] += time.time() - exact_start

                    # If exact match is good enough, use it
                    if exact_score >= similarity_threshold:
                        cv_result.similarity_score = exact_score
                        cv_result.matched_keywords = exact_matches
                        cv_result.number_of_matches = number_of_matches
                        cv_result.match_type = "exact"
                        search_results.append(cv_result)
                        print(
                            f"✅ EXACT {i}: {cv_result.applicant_profile.full_name} - Score: {exact_score:.3f}")
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
                        cv_result.number_of_matches = len(fuzzy_matches)
                        cv_result.match_type = "fuzzy"
                        search_results.append(cv_result)
                        print(
                            f"✅ FUZZY {i}: {cv_result.applicant_profile.full_name} - Score: {fuzzy_score:.3f}")

                    cv_result.loaded_cv_index = i

                except Exception as e:
                    print(f"❌ Error processing CV {i}: {e}")
                    continue

            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)

            # Return top matches with timing info
            top_results = search_results[:top_matches]

            print(
                f"Timing - Exact: {search_times['exact']:.3f}s, Fuzzy: {search_times['fuzzy']:.3f}s")

            # Store timing info for UI display
            for result in top_results:
                result.search_timing = search_times

            return top_results

        except Exception as e:
            print(f"❌ Error searching CVs: {e}")
            return []

    def _calculate_exact_match_score(self, cv_text: str, keywords: List[str], algorithm: str) -> tuple:
        """CALCULATE: Exact match score using your algorithms"""
        try:
            cv_text_lower = cv_text.lower()
            keyword_counts = {}
            total_matches = 0

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Use your algorithms
                if algorithm == "kmp":
                    matches = self.string_matcher.kmp_search(
                        cv_text_lower, keyword_lower)
                elif algorithm == "bm":
                    matches = self.string_matcher.boyer_moore_search(
                        cv_text_lower, keyword_lower)
                else:  # regex or fallback
                    import re
                    matches = len(re.findall(
                        re.escape(keyword_lower), cv_text_lower))
                    matches = [0] if matches > 0 else []

                if matches:
                    match_count = len(matches)
                    # If keyword already found before, add to existing count
                    if keyword in keyword_counts:
                        keyword_counts[keyword] += match_count
                    else:
                        # First time finding this keyword, set count to match_count
                        keyword_counts[keyword] = match_count

                    total_matches += match_count

            # Convert dictionary to list of tuples
            matched_keywords = [(keyword, count)
                                for keyword, count in keyword_counts.items()]

            # Calculate score
            if len(keywords) > 0:
                keyword_match_ratio = len(matched_keywords) / len(keywords)
                frequency_bonus = min(total_matches * 0.1, 1.0)
                score = keyword_match_ratio * 0.7 + frequency_bonus * 0.3
                return score, matched_keywords, total_matches

            return 0.0, [], 0

        except Exception as e:
            print(f"⚠️ Error in exact match calculation: {e}")
            return 0.0, []

    def _calculate_fuzzy_match_score(self, cv_text: str, keywords: List[str], threshold: float) -> tuple:
        try:
            cv_words = cv_text.lower().split()
            keyword_counts = {}  # Dictionary to track keyword fuzzy matches
            total_similarity = 0

            for keyword in keywords:
                keyword_lower = keyword.lower()
                best_similarity = 0
                best_match = None

                for word in cv_words:
                    if len(word) >= 3:  # Only check words with 3+ chars
                        similarity = self.string_matcher.calculate_similarity(
                            keyword_lower, word) / 100.0
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = word

                if best_similarity >= threshold:
                    match_key = best_match
                    if match_key in keyword_counts:
                        keyword_counts[match_key] += 1
                    else:
                        keyword_counts[match_key] = 1

                    total_similarity += best_similarity

            matched_keywords = [(match_key, count)
                                for match_key, count in keyword_counts.items()]

            # Calculate final score
            if len(keywords) > 0:
                keyword_match_ratio = len(matched_keywords) / len(keywords)
                avg_similarity = total_similarity / \
                    len(keywords) if matched_keywords else 0
                score = keyword_match_ratio * 0.6 + avg_similarity * 0.4
                return score, matched_keywords

            return 0.0, []

        except Exception as e:
            print(f"⚠️ Error in fuzzy match calculation: {e}")
            return 0.0, []

    def get_cv_summary_statistics(self) -> Dict[str, Any]:
        """Get CV summary statistics"""
        try:
            # Total CVs
            total_query = "SELECT COUNT(*) as total FROM ApplicationDetail"
            total_result = self.db.execute_query(total_query)
            total_cvs = total_result[0]['total'] if total_result else 0

            # Role breakdown
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

                # Prepare data for multiprocessing
                cv_tasks = []
                for row in results:
                    try:
                        cv_tasks.append({
                            'applicant_id': row['applicant_id'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'date_of_birth': row['date_of_birth'],
                            'address': row['address'],
                            'phone_number': row['phone_number'],
                            'detail_id': row['detail_id'],
                            'application_role': row['application_role'],
                            'cv_path': row['cv_path']
                        })
                    except Exception as e:
                        print(f"⚠️ Error preparing CV data: {e}")
                        continue

                # Use multiprocessing for PDF parsing
                max_workers = min(mp.cpu_count(), len(cv_tasks))

                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    futures = [executor.submit(
                        self._process_single_cv, task) for task in cv_tasks]

                    # Collect results
                    completed_count = 0
                    for future in as_completed(futures):
                        try:
                            cv_result = future.result()
                            if cv_result:
                                cv_results.append(cv_result)
                            completed_count += 1

                            # Progress indicator
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

            self.loaded_cvs = cv_results  # Cache loaded CVs
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

            # Create objects
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

            # Load CV content
            pdf_parser = PDFParser()

            # Get file path (replicate the _get_cv_file_path logic)
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
