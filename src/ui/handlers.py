from src.database.repository import CVRepository
from src.utils.pdf_parser import PDFParser
from src.utils.cv_extractor import CVExtractor, CVSummary
import flet as ft
import os
import sys
import time

project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class UIHandlers:
    def __init__(self, page: ft.Page):
        """Initialize  UI handlers"""
        self.page = page
        self.repo = CVRepository()

        # UI components
        self.keywords_input = None
        self.algorithm_radio = None
        self.top_matches_input = None
        self.results_container = None
        self.status_text = None
        self.progress_ring = None

    def create_components(self):
        """Create  UI components"""

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
                ft.Radio(value="aho", label="Aho–Corasick"),
            ]),
            value="kmp"
        )
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
            'results_container': self.results_container,
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

            search_start = time.time()
            results = self.repo.search_cvs_by_keywords(
                keywords=keywords,
                algorithm=algorithm,
                top_matches=top_matches,
            )
            search_time = time.time() - search_start
            self.repo.disconnect()

            # Extract search timing information from results
            search_timing = None
            if results and hasattr(results[0], 'search_timing'):
                search_timing = results[0].search_timing

            # Create timing display
            if search_timing:
                timing_row = ft.Row([
                    ft.Column([
                        ft.Text("Algorithm", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(algorithm.upper(), size=14,
                                color=ft.Colors.BLUE_600)
                    ]),
                    ft.Column([
                        ft.Text("Exact Search", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{search_timing['exact']:.3f}s", size=14, color=ft.Colors.GREEN_600)
                    ]),
                    ft.Column([
                        ft.Text("Fuzzy Search", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{search_timing['fuzzy']:.3f}s", size=14, color=ft.Colors.ORANGE_600)
                    ]),
                    ft.Column([
                        ft.Text("Total Time", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(f"{search_time:.3f}s", size=14,
                                color=ft.Colors.PURPLE_600)
                    ]),
                    ft.Column([
                        ft.Text("Found", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(str(len(results)), size=14,
                                color=ft.Colors.RED_600)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            else:
                # Fallback to original timing display if search_timing not available
                timing_row = ft.Row([
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
                        ft.Text("Found", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(str(len(results)), size=14,
                                color=ft.Colors.ORANGE_600)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

            summary_card = ft.Container(
                content=ft.Column([
                    ft.Text(f"SEARCH RESULTS for '{keywords}'", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                    timing_row
                ], spacing=10),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=10,
                padding=15,
                border=ft.border.all(2, ft.Colors.ORANGE_300),
                margin=ft.margin.only(bottom=15)
            )

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

    def create_result_card(self, result, index):
        """Create a result card with click handler for CV summary"""

        def on_card_click(e):
            """Handle card click to show CV summary"""
            self.show_cv_summary(result, index)

        # Create clickable result card
        result_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(
                        content=ft.Text(
                            f"{index}", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.BLUE_600,
                        radius=20
                    ),
                    ft.Column([
                        ft.Text(result.applicant_profile.full_name,
                                size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Role: {result.application_detail.application_role}",
                                size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"Matches: {result.total_matches}",
                                size=12, color=ft.Colors.GREEN_600),
                    ], expand=True, spacing=2),
                    ft.Column([
                        ft.Icon(ft.icons.VISIBILITY,
                                color=ft.Colors.BLUE_600, size=20),
                        ft.Text("Click to view", size=10,
                                color=ft.Colors.BLUE_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Matched keywords
                ft.Container(
                    content=ft.Column([
                        ft.Text("Matched Keywords:", size=12,
                                weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    f"{kw[0]} ({kw[1]})" if isinstance(
                                        kw, tuple) else str(kw),
                                    size=10, color=ft.Colors.WHITE
                                ),
                                bgcolor=ft.Colors.ORANGE_600,
                                padding=ft.padding.symmetric(
                                    horizontal=6, vertical=2),
                                border_radius=10,
                                margin=ft.margin.all(1)
                            ) for kw in (result.matched_keywords[:5] if result.matched_keywords else [])
                        ])
                    ]),
                    margin=ft.margin.only(top=10)
                )
            ], spacing=5),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=10),
            border=ft.border.all(2, ft.Colors.BLUE_200),
            ink=True,  # Add ripple effect
            on_click=on_card_click,  # Add click handler
        )

        return result_card

    def show_cv_summary(self, cv_result, result_index):
        """Show CV summary dialog when result is clicked"""
        from utils.cv_extractor import CVExtractor

        def close_summary_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def show_full_cv(e):
            """Show full CV text in a dialog"""
            full_cv_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Full CV - {cv_result.applicant_profile.full_name}",
                              size=18, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(cv_result.cv_text,
                                size=12,
                                selectable=True,
                                overflow=ft.TextOverflow.FADE),
                    ],
                        scroll=ft.ScrollMode.AUTO,
                        height=500),
                    width=800,
                    height=500
                ),
                actions=[
                    ft.TextButton("Close", on_click=close_summary_dialog)
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.dialog = full_cv_dialog
            full_cv_dialog.open = True
            self.page.update()

        def view_original_pdf(e):
            """Open the original PDF file"""
            try:
                import os
                import subprocess
                import platform
                from pathlib import Path

                # Get the CV path from the application detail
                cv_path = cv_result.application_detail.cv_path
                if not cv_path:
                    self.show_error_dialog("PDF file path not available")
                    return

                # Construct the full file path
                clean_path = cv_path.strip('/\\')
                project_root = Path(__file__).parent.parent.parent
                full_pdf_path = str(project_root / clean_path)

                # Check if file exists
                if not os.path.exists(full_pdf_path):
                    self.show_error_dialog(f"PDF file not found: {full_pdf_path}")
                    return

                # Open PDF with default system viewer
                system = platform.system()
                try:
                    if system == "Windows":
                        os.startfile(full_pdf_path)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["open", full_pdf_path])
                    elif system == "Linux":
                        subprocess.run(["xdg-open", full_pdf_path])
                    else:
                        self.show_error_dialog("Unsupported operating system")

                    # Close the summary dialog after opening PDF
                    close_summary_dialog(e)

                except Exception as open_error:
                    self.show_error_dialog(f"Failed to open PDF: {str(open_error)}")

            except Exception as ex:
                self.show_error_dialog(f"Error viewing PDF: {str(ex)}")

        # Extract CV summary using CVExtractor
        cv_summary = CVExtractor.extract_full_summary(cv_result.cv_text, personal_info=cv_result.applicant_profile)

        # Create summary dialog content
        summary_content = ft.Column([
            # Header with applicant info
            ft.Container(
                content=ft.Column([
                    ft.Text("CV Summary", size=20,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                bgcolor=ft.Colors.BLUE_700,
                padding=15,
                border_radius=ft.BorderRadius(10, 10, 0, 0),
                margin=ft.margin.only(bottom=10)
            ),

            # Personal Information Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Personal Information", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ft.Divider(height=1, color=ft.Colors.BLUE_200),
                    ft.Row([
                        ft.Column([
                            ft.Text("Name:", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(
                                cv_result.applicant_profile.full_name, size=14),
                        ], expand=1),
                        ft.Column([
                            ft.Text(
                                "Phone:", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(
                                cv_summary.phone or cv_result.applicant_profile.phone_number or "Not available", size=14),
                        ], expand=1),
                    ]),
                    ft.Row([
                        ft.Column([
                            ft.Text(
                                "Address:", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(cv_summary.address or cv_result.applicant_profile.address or "Not available",
                                    size=14, overflow=ft.TextOverflow.ELLIPSIS),
                        ], expand=1),
                        ft.Column([
                            ft.Text("Role Applied:",
                                    weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(
                                cv_result.application_detail.application_role, size=14),
                        ], expand=1),
                    ]),
                ]),
                bgcolor=ft.Colors.BLUE_50,
                padding=15,
                border_radius=10,
                margin=ft.margin.only(bottom=10)
            ),

            # Professional Summary Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Professional Summary", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ft.Divider(height=1, color=ft.Colors.GREEN_200),
                    ft.Text(cv_summary.summary or "No summary available",
                            size=14, overflow=ft.TextOverflow.FADE),
                ]),
                bgcolor=ft.Colors.GREEN_50,
                padding=15,
                border_radius=10,
                margin=ft.margin.only(bottom=10)
            ),

            # Skills Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Skills", size=16, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PURPLE_700),
                    ft.Divider(height=1, color=ft.Colors.PURPLE_200),
                    ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    skill, size=12, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.PURPLE_600,
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=15,
                                margin=ft.margin.all(2)
                                # Group skills in rows of 3
                            ) for skill in cv_summary.skills[i:i+3]
                            # Max 3 rows of 3 skills
                        ]) for i in range(0, min(len(cv_summary.skills), 9), 3)
                    ] if cv_summary.skills else [ft.Text("No skills extracted", size=14, color=ft.Colors.GREY_600)]),
                ]),
                bgcolor=ft.Colors.PURPLE_50,
                padding=15,
                border_radius=10,
                margin=ft.margin.only(bottom=10)
            ),            # Experience Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Work Experience", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                    ft.Divider(height=1, color=ft.Colors.ORANGE_200),
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Experience {i+1}",
                                        size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800),
                                ft.Text(str(exp), size=14, selectable=True),
                            ]),
                            bgcolor=ft.Colors.WHITE,
                            padding=10,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.ORANGE_200),
                            margin=ft.margin.only(bottom=5)
                            # Show max 3 experiences
                        ) for i, exp in enumerate(cv_summary.experience[:3])
                    ] if cv_summary.experience else [ft.Text("No experience extracted", size=14, color=ft.Colors.GREY_600)]),
                ]),
                bgcolor=ft.Colors.ORANGE_50,
                padding=15,
                border_radius=10,
                margin=ft.margin.only(bottom=10)
            ),            # Education Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Education", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_700),
                    ft.Divider(height=1, color=ft.Colors.CYAN_200),
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    f"Education {i+1}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_800),
                                ft.Text(str(edu), size=14, selectable=True),
                            ]),
                            bgcolor=ft.Colors.WHITE,
                            padding=10,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.CYAN_200),
                            margin=ft.margin.only(bottom=5)
                        ) for i, edu in enumerate(cv_summary.education)
                    ] if cv_summary.education else [ft.Text("No education extracted", size=14, color=ft.Colors.GREY_600)]),
                ]),
                bgcolor=ft.Colors.CYAN_50,
                padding=15,
                border_radius=10,
                margin=ft.margin.only(bottom=15)
            ),

            # Matched Keywords Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Matched Keywords", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ft.Divider(height=1, color=ft.Colors.RED_200),
                    ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"{keyword[0]} ({keyword[1]})" if isinstance(keyword, tuple) else str(keyword),
                                                size=12, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.RED_600,
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=4),
                                border_radius=15,
                                margin=ft.margin.all(2)
                                # Group keywords in rows of 2
                            ) for keyword in cv_result.matched_keywords[i:i+2]
                            # Max 4 rows of 2 keywords
                        ]) for i in range(0, min(len(cv_result.matched_keywords), 8), 2)
                    ] if cv_result.matched_keywords else [ft.Text("No keywords matched", size=14, color=ft.Colors.GREY_600)]),
                ]),
                bgcolor=ft.Colors.RED_50,
                padding=15,
                border_radius=10,
            ),
        ], scroll=ft.ScrollMode.AUTO)

        # Create summary dialog
        summary_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text(f"CV Summary - {cv_result.applicant_profile.full_name}",
                        size=18, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    on_click=close_summary_dialog,
                    tooltip="Close"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=summary_content,
                width=700,
                height=600
            ),            actions=[
                ft.ElevatedButton(
                    "View Original PDF",
                    icon=ft.icons.PICTURE_AS_PDF,
                    on_click=view_original_pdf,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
                ),
                ft.ElevatedButton(
                    "View Full CV Text",
                    icon=ft.icons.DESCRIPTION,
                    on_click=show_full_cv,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                ),
                ft.TextButton("Close", on_click=close_summary_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.page.dialog = summary_dialog
        summary_dialog.open = True
        self.page.update()

    def show_error_dialog(self, message):
        """Show error dialog with the given message"""
        def close_error_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.ERROR, color=ft.Colors.RED_600),
                ft.Text("Error", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
            ]),
            content=ft.Container(
                content=ft.Text(message, size=14),
                width=400
            ),
            actions=[
                ft.TextButton("OK", on_click=close_error_dialog)
            ],
        )

        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()
