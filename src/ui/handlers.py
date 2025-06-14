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
        self.results_container = None  # Changed from results_text to results_container
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
        )        # Results display container
        self.results_container = ft.Column(
            controls=[
                ft.Text(
                    "Results will appear here...",
                    size=14,
                    color=ft.Colors.GREY_600
                )
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )

        # Status and progress
        self.status_text = ft.Text("Ready", size=12, color=ft.Colors.GREEN)
        self.progress_ring = ft.ProgressRing(visible=False)
        return {
            'keywords_input': self.keywords_input,
            'algorithm_radio': self.algorithm_radio,
            'top_matches_input': self.top_matches_input,
            'results_container': self.results_container,  # Changed from results_text
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
                stats_card = ft.Container(
                    content=ft.Column([
                        ft.Text("DATABASE STATISTICS", size=16,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Divider(),
                        ft.Row([
                            ft.Column([
                                ft.Text("Total CVs", size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(str(stats['total_cvs']),
                                        size=20, color=ft.Colors.BLUE_600)
                            ]),
                            ft.Column([
                                ft.Text("Total Roles", size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(str(stats['total_roles']),
                                        size=20, color=ft.Colors.GREEN_600)
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        ft.Text("Role Breakdown:", size=14,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Column([
                            ft.Text(f"• {role}: {count} CVs", size=12)
                            # Show top 10
                            for role, count in list(stats['role_breakdown'].items())[:10]
                        ])
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=15,
                    border=ft.border.all(2, ft.Colors.BLUE_300)
                )

                self.results_container.controls = [stats_card]
            else:
                self.status_text.value = "❌ Database connection failed"
                self.status_text.color = ft.Colors.RED
                error_card = ft.Container(
                    content=ft.Text("Could not connect to database. Check your connection settings.",
                                    size=14, color=ft.Colors.RED_700),
                    bgcolor=ft.Colors.RED_50,
                    border_radius=10,
                    padding=15,
                    border=ft.border.all(2, ft.Colors.RED_300)
                )
                self.results_container.controls = [error_card]

            self.page.update()
        except Exception as e:
            self.status_text.value = f"❌ Error: {str(e)}"
            self.status_text.color = ft.Colors.RED
            error_card = ft.Container(
                content=ft.Text(f"Database test error: {str(e)}",
                                size=14, color=ft.Colors.RED_700),
                bgcolor=ft.Colors.RED_50,
                border_radius=10,
                padding=15,
                border=ft.border.all(2, ft.Colors.RED_300)
            )
            self.results_container.controls = [error_card]
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

            # Create search summary card
            summary_card = ft.Container(
                content=ft.Column([
                    ft.Text(f"SEARCH RESULTS for '{keywords}'", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                    ft.Row([
                        ft.Column([
                            ft.Text("Algorithm", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(algorithm.upper(), size=14,
                                    color=ft.Colors.BLUE_600)
                        ]),
                        ft.Column([
                            ft.Text("Search Time", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(f"{search_time:.3f}s", size=14,
                                    color=ft.Colors.GREEN_600)
                        ]),
                        ft.Column([
                            ft.Text("Requested", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(str(top_matches), size=14,
                                    color=ft.Colors.PURPLE_600)
                        ]),
                        ft.Column([
                            ft.Text("Found", size=12,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(str(len(results)), size=14,
                                    color=ft.Colors.ORANGE_600)
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                ], spacing=10),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=10,
                padding=15,
                border=ft.border.all(2, ft.Colors.ORANGE_300),
                margin=ft.margin.only(bottom=15)
            )

            # Create result cards
            result_cards = [summary_card]

            if results:
                for i, result in enumerate(results, 1):
                    result_card = self.create_result_card(result, i)
                    result_cards.append(result_card)
            else:
                no_results_card = ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SEARCH_OFF, size=48,
                                color=ft.Colors.GREY_400),
                        ft.Text("No matches found", size=16,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                        ft.Text("Try different keywords or algorithms",
                                size=12, color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    padding=30,
                    border=ft.border.all(2, ft.Colors.GREY_300)
                )
                result_cards.append(no_results_card)

            self.results_container.controls = result_cards
            self.status_text.value = f"✅ Search completed: {len(results)} results"
            self.status_text.color = ft.Colors.GREEN
        except Exception as e:
            error_card = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR, size=48, color=ft.Colors.RED_400),
                    ft.Text("Search Error", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ft.Text(str(e), size=12, color=ft.Colors.RED_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                bgcolor=ft.Colors.RED_50,
                border_radius=10,
                padding=30,
                border=ft.border.all(2, ft.Colors.RED_300)
            )
            self.results_container.controls = [error_card]
            self.status_text.value = f"❌ Search failed: {str(e)}"
            self.status_text.color = ft.Colors.RED

        finally:
            self.progress_ring.visible = False
            self.page.update()

    def clear_results(self, e=None):
        self.results_container.controls = [
            ft.Text(
                "Results cleared. Ready for new search.",
                size=14,
                color=ft.Colors.GREY_600
            )
        ]
        self.keywords_input.value = ""
        self.top_matches_input.value = "10"
        self.status_text.value = "Ready"
        self.status_text.color = ft.Colors.GREEN
        self.page.update()

    def create_result_card(self, result, index: int) -> ft.Container:
        """Create a card component for a single CV search result"""
        profile = result.applicant_profile
        app = result.application_detail
        score = getattr(result, 'similarity_score', 0)
        match_type = getattr(result, 'match_type', 'exact')
        matched_kw = getattr(result, 'matched_keywords', [])

        # Handle tuple format (keyword, count)
        if matched_kw and isinstance(matched_kw[0], tuple):
            matches_display = [f"{kw}({count})" for kw, count in matched_kw]
            matches_text = ', '.join(matches_display)
        else:
            # Fallback for old format
            matches_text = ', '.join(str(kw) for kw in matched_kw)

        # Color coding based on score
        if score >= 0.8:
            card_color = ft.Colors.GREEN_50
            border_color = ft.Colors.GREEN_400
            score_color = ft.Colors.GREEN_700
        elif score >= 0.5:
            card_color = ft.Colors.ORANGE_50
            border_color = ft.Colors.ORANGE_400
            score_color = ft.Colors.ORANGE_700
        else:
            card_color = ft.Colors.RED_50
            border_color = ft.Colors.RED_400
            score_color = ft.Colors.RED_700

        return ft.Container(
            content=ft.Column([
                # Header row with name and score
                ft.Row([
                    ft.Column([
                        ft.Text(
                            f"{index}. {profile.full_name}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800
                        ),
                        ft.Text(
                            app.application_role,
                            size=14,
                            color=ft.Colors.GREY_700
                        )
                    ], expand=True),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"{score:.3f}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=score_color
                            ),
                            ft.Text(
                                match_type.upper(),
                                size=10,
                                color=ft.Colors.GREY_600
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=10
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Matched keywords section
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Matched Keywords:",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_700
                        ),
                        ft.Text(
                            matches_text if matches_text else "No matches",
                            size=12,
                            color=ft.Colors.BLUE_600,
                            selectable=True
                        )
                    ]),
                    padding=ft.padding.only(top=5)
                ),

                # Contact info (expandable)
                ft.ExpansionTile(
                    title=ft.Text("Contact Information", size=12),
                    controls=[
                        ft.Text(f"📧 ID: {profile.applicant_id}", size=11),
                        ft.Text(f"📍 Address: {profile.address}", size=11),
                        ft.Text(f"📞 Phone: {profile.phone_number}", size=11),
                        ft.Text(f"🎂 DOB: {profile.date_of_birth}", size=11),
                    ],
                    initially_expanded=False
                )
            ], spacing=8),
            bgcolor=card_color,
            border=ft.border.all(2, border_color),
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=10)
        )
