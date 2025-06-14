from utils.cv_extractor import CVExtractor, CVSummary
from utils.pdf_parser import PDFParser
import flet as ft
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Replace relative import with absolute
try:
    from database.repository import CVRepository
except ImportError:
    from src.database.repository import CVRepository


class UIHandlers:
    def __init__(self, page: ft.Page):
        """Initialize  UI handlers"""
        self.page = page
        self.repo = CVRepository()

        # UI components
        self.keywords_input = None
        self.algorithm_radio = None
        self.top_matches_input = None
        self.results_text = None
        self.status_text = None
        self.progress_ring = None

    def create_components(self):
        """Create  UI components"""        # Keywords input
        self.keywords_input = ft.TextField(
            label="Enter keywords (comma-separated)",
            hint_text="e.g., python, javascript, sql",
            width=400
        )

        # Top matches input
        self.top_matches_input = ft.TextField(
            label="Number of top matches",
            hint_text="Default: 10",
            value="10",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Algorithm selection
        self.algorithm_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="kmp", label="KMP"),
                ft.Radio(value="bm", label="Boyer-Moore"),
            ]),
            value="kmp"
        )

        # Results display
        self.results_text = ft.Text(
            "Results will appear here...",
            size=12,
            selectable=True
        )

        # Status and progress
        self.status_text = ft.Text("Ready", size=12, color=ft.Colors.GREEN)
        self.progress_ring = ft.ProgressRing(visible=False)
        return {
            'keywords_input': self.keywords_input,
            'algorithm_radio': self.algorithm_radio,
            'top_matches_input': self.top_matches_input,
            'results_text': self.results_text,
            'status_text': self.status_text,
            'progress_ring': self.progress_ring
        }

    def test_database_connection_and_load(self, e=None):
        try:
            self.status_text.value = "Testing database connection and loading cvs..."
            self.status_text.color = ft.Colors.BLUE
            self.page.update()

            if self.repo.connect():
                stats = self.repo.get_statistics()
                self.repo.get_all_cvs()
                self.repo.disconnect()

                self.status_text.value = f"✅ Connected! Found {stats['total_cvs']} CVs"
                self.status_text.color = ft.Colors.GREEN

                # Show stats in results
                result_text = f"DATABASE STATISTICS:\n"
                result_text += f"Total CVs: {stats['total_cvs']}\n"
                result_text += f"Total Roles: {stats['total_roles']}\n\n"
                result_text += "Role Breakdown:\n"
                for role, count in stats['role_breakdown'].items():
                    result_text += f"  • {role}: {count} CVs\n"

                self.results_text.value = result_text
            else:
                self.status_text.value = "❌ Database connection failed"
                self.status_text.color = ft.Colors.RED
                self.results_text.value = "Could not connect to database. Check your connection settings."

            self.page.update()

        except Exception as e:
            self.status_text.value = f"❌ Error: {str(e)}"
            self.status_text.color = ft.Colors.RED
            self.results_text.value = f"Database test error: {str(e)}"
            self.page.update()

    def search_cvs(self, e=None):
        try:
            keywords = self.keywords_input.value.strip() if self.keywords_input.value else ""
            algorithm = self.algorithm_radio.value if self.algorithm_radio.value else "kmp"

            try:
                top_matches_str = self.top_matches_input.value.strip(
                ) if self.top_matches_input.value else "10"
                top_matches = int(top_matches_str) if top_matches_str else 10
                if top_matches <= 0:
                    top_matches = 10
            except ValueError:
                top_matches = 10
                self.top_matches_input.value = "10"
                self.page.update()

            if not keywords:
                self.status_text.value = "❌ Please enter keywords"
                self.status_text.color = ft.Colors.RED
                self.page.update()
                return

            self.progress_ring.visible = True
            self.status_text.value = f"Searching with {algorithm.upper()}... (top {top_matches})"
            self.status_text.color = ft.Colors.BLUE
            self.page.update()

            if not self.repo.connect():
                self.status_text.value = "❌ Cannot connect to database"
                self.status_text.color = ft.Colors.RED
                self.progress_ring.visible = False
                self.page.update()
                return

            # Perform search
            search_start = time.time()
            results = self.repo.search_cvs_by_keywords(
                keywords=keywords,
                algorithm=algorithm,
                top_matches=top_matches,
                similarity_threshold=0.3
            )
            search_time = time.time() - search_start

            self.repo.disconnect()

            # Display results
            result_text = f"SEARCH RESULTS for '{keywords}' using {algorithm.upper()}:\n\n"
            result_text += f"Search Time: {search_time:.3f} seconds\n"
            result_text += f"Top Matches Requested: {top_matches}\n"
            result_text += f"Results Found: {len(results)}\n\n"

            if results:
                for i, result in enumerate(results, 1):
                    profile = result.applicant_profile
                    app = result.application_detail
                    score = getattr(result, 'similarity_score', 0)
                    match_type = getattr(result, 'match_type', 'exact')
                    matched_kw = getattr(result, 'matched_keywords', [])

                    result_text += f"{i}. {profile.full_name}\n"
                    result_text += f"   Role: {app.application_role}\n"
                    result_text += f"   Score: {score:.3f} ({match_type})\n"

                    # Handle tuple format (keyword, count)
                    if matched_kw and isinstance(matched_kw[0], tuple):
                        matches_display = [
                            f"{kw}({count})" for kw, count in matched_kw]
                        result_text += f"   Matched: {', '.join(matches_display)}\n"
                    else:
                        # Fallback for old format
                        result_text += f"   Matched: {', '.join(str(kw) for kw in matched_kw)}\n"
            else:
                result_text += "No matches found.\n"

            self.results_text.value = result_text
            self.status_text.value = f"✅ Search completed: {len(results)} results"
            self.status_text.color = ft.Colors.GREEN

        except Exception as e:
            self.results_text.value = f"Search error: {str(e)}"
            self.status_text.value = f"❌ Search failed: {str(e)}"
            self.status_text.color = ft.Colors.RED

        finally:
            self.progress_ring.visible = False
            self.page.update()

    def clear_results(self, e=None):
        self.results_text.value = "Results cleared."
        self.keywords_input.value = ""
        self.top_matches_input.value = "10"
        self.status_text.value = "Ready"
        self.status_text.color = ft.Colors.GREEN
        self.page.update()
