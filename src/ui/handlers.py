from models.database_models import CVSearchResult
from utils.text_preprocessor import TextPreprocessor
from utils.cv_extractor import CVExtractor, CVSummary
from utils.file_handler import FileHandler
from utils.pdf_parser import PDFParser
from algorithms.string_matcher import StringMatcher
from models.cv_match import CVMatch
import flet as ft
import os
import sys
import time
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Replace relative import with absolute
try:
    from database.repository import CVRepository
except ImportError:
    from src.database.repository import CVRepository


class UIHandlers:
    def __init__(self, page: ft.Page):
        """Initialize UI handlers with page reference"""
        self.page = page

        # Initialize repositories - try encrypted first, fallback to regular
        try:
            from database.encrypted_repository import EncryptedCVRepository
            self.repo = EncryptedCVRepository()
            self.encryption_enabled = True
            print("🔐 Using encrypted repository")
        except ImportError:
            from database.repository import CVRepository
            self.repo = CVRepository()
            self.encryption_enabled = False
            print("📝 Using standard repository")

        # Initialize other attributes
        self.keywords_input = None
        self.algorithm_radio = None
        self.top_matches_dropdown = None
        self.similarity_slider = None
        self.results_container = None
        self.summary_container = None
        self.full_text_container = None
        self.highlights_container = None
        self.status_text = None
        self.progress_ring = None

        # Initialize CV storage
        self.parsed_cvs = {}
        self.cv_summaries = {}

    def create_file_picker(self, page: ft.Page):
        """Create and setup file picker"""
        file_picker = ft.FilePicker(
            on_result=self.handle_file_selection
        )
        page.overlay.append(file_picker)
        return file_picker

    def setup_ui_components(self):
        """Setup all UI components according to specifications"""
        # Algorithm selection
        algorithm_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="kmp", label="Knuth-Morris-Pratt (KMP)"),
                ft.Radio(value="bm", label="Boyer-Moore"),
                ft.Radio(value="regex", label="Regex Search")
            ]),
            value="kmp"
        )

        # Keywords input
        keywords_input = ft.TextField(
            label="Enter keywords (comma-separated)",
            hint_text="e.g., python, react, javascript, sql",
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=400
        )

        # Top Matches Selector
        top_matches_dropdown = ft.Dropdown(
            label="Top Matches",
            value="10",
            options=[
                ft.dropdown.Option("5", "Top 5"),
                ft.dropdown.Option("10", "Top 10"),
                ft.dropdown.Option("15", "Top 15"),
                ft.dropdown.Option("20", "Top 20"),
            ],
            width=150
        )

        # Similarity threshold (convert to 0-1 range)
        similarity_slider = ft.Slider(
            min=0,
            max=1,
            divisions=20,
            value=0.3,
            label="Similarity Threshold: {value:.2f}",
            width=300
        )

        similarity_text = ft.Text("Similarity Threshold: 0.30", size=14)

        def update_similarity_text(e):
            similarity_text.value = f"Similarity Threshold: {similarity_slider.value:.2f}"
            similarity_text.update()

        similarity_slider.on_change = update_similarity_text

        selected_files_text = ft.Text(
            "No files selected", size=14, color=ft.Colors.GREY_600)

        # Summary Result Section
        summary_column = ft.Column([
            ft.Text("Performance summary will appear here...", size=12)
        ])

        summary_container = ft.Container(
            content=summary_column,  # Wrap Column in Container
            border=ft.border.all(1, ft.Colors.BLUE_400),
            border_radius=5,
            padding=10,
            height=120,
            expand=True
        )

        results_column = ft.Column([
            ft.Text("Search results will appear here...", size=12)
        ], scroll=ft.ScrollMode.AUTO)

        results_container = ft.Container(
            content=results_column,  # Wrap Column in Container
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=300,
            expand=True
        )

        full_text_column = ft.Column([
            ft.Text("Full CV content will appear here...", size=12)
        ], scroll=ft.ScrollMode.AUTO)

        full_text_container = ft.Container(
            content=full_text_column,  # Wrap Column in Container
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=300,
            expand=True
        )

        highlights_column = ft.Column([
            ft.Text("CV Summary / Highlights will appear here...", size=12)
        ], scroll=ft.ScrollMode.AUTO)

        highlights_container = ft.Container(
            content=highlights_column,  # Wrap Column in Container
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=400,
            expand=True
        )

        progress_ring = ft.ProgressRing(visible=False)
        status_text = ft.Text("", size=12, color=ft.Colors.BLUE_600)

        # Store references to the COLUMNS, not containers
        self.summary_container = summary_column      # ✅ Store Column, not Container
        self.results_container = results_column      # ✅ Store Column, not Container
        self.full_text_container = full_text_column  # ✅ Store Column, not Container
        self.highlights_container = highlights_column  # ✅ Store Column, not Container

        return {
            'algorithm_radio': algorithm_radio,
            'keywords_input': keywords_input,
            'top_matches_dropdown': top_matches_dropdown,
            'similarity_slider': similarity_slider,
            'similarity_text': similarity_text,
            'selected_files_text': selected_files_text,
            'summary_container': summary_container,      # Return Container for UI
            'results_container': results_container,      # Return Container for UI
            'full_text_container': full_text_container,  # Return Container for UI
            'highlights_container': highlights_container,  # Return Container for UI
            'progress_ring': progress_ring,
            'status_text': status_text
        }

    def pick_files(self, e, file_picker):
        """Handle file picker button click"""
        file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=["pdf"]
        )

    def handle_file_selection(self, e: ft.FilePickerResultEvent):
        """Handle file selection with text preprocessing and information extraction"""
        if e.files:
            self.selected_files_text.value = f"Selected {len(e.files)} PDF file(s)"
            self.selected_files_text.color = ft.Colors.GREEN_600
            self.selected_files_text.update()

            self.progress_ring.visible = True
            self.status_text.value = "Parsing PDF files and extracting information..."
            self.status_text.update()

            self.parsed_cvs.clear()
            self.cv_summaries.clear()

            for file in e.files:
                file_path = file.path
                filename = os.path.basename(file_path)

                # Parse PDF with multiple text variants
                pdf_variants = PDFParser.parse_pdf_with_variants(file_path)

                if pdf_variants:
                    self.parsed_cvs[filename] = pdf_variants

                    # Extract CV information using regex - REQUIRED BY SPEC
                    cv_summary = CVExtractor.extract_full_summary(
                        pdf_variants['original'])
                    self.cv_summaries[filename] = cv_summary

                    # Save original and flattened text
                    FileHandler.save_parsed_text(
                        pdf_variants['original'], filename)
                    FileHandler.save_parsed_text(
                        pdf_variants['flattened'],
                        f"{os.path.splitext(filename)[0]}_flattened"
                    )

            self.display_all_cvs()

            self.progress_ring.visible = False
            self.status_text.value = f"Successfully parsed {len(self.parsed_cvs)} CV(s) with information extraction"
            self.status_text.update()
        else:
            self.selected_files_text.value = "No files selected"
            self.selected_files_text.color = ft.Colors.GREY_600
            self.selected_files_text.update()

    def display_all_cvs(self):
        """Display all parsed CV content with extracted information"""
        if not self.parsed_cvs:
            self.full_text_container.content = ft.Column([
                ft.Text("Full CV content will appear here...", size=12)
            ], scroll=ft.ScrollMode.AUTO)
        else:
            cv_widgets = []
            for i, (filename, variants) in enumerate(self.parsed_cvs.items(), 1):
                original_content = variants['original']
                flattened_preview = variants['flattened'][:200] + "..." if len(
                    variants['flattened']) > 200 else variants['flattened']

                # Display extracted summary
                summary = self.cv_summaries.get(filename, CVSummary())

                cv_widgets.extend([
                    ft.Text(f"CV #{i}: {filename}",
                            size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600),
                    ft.Text(f"👤 Extracted Name: {summary.name}",
                            size=12, color=ft.Colors.GREEN_600),
                    ft.Text(f"📧 Email: {summary.email}",
                            size=12, color=ft.Colors.GREEN_600),
                    ft.Text(f"📞 Phone: {summary.phone}",
                            size=12, color=ft.Colors.GREEN_600),
                    ft.Text(f"🔧 Skills: {', '.join(summary.skills[:5])}",
                            size=12, color=ft.Colors.PURPLE_600),
                    ft.Divider(),
                    ft.Text(f"📄 Original Content:", size=12,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(original_content[:500] + "..." if len(original_content) > 500 else original_content,
                            size=12, selectable=True),
                    ft.Divider(),
                    ft.Text(f"🔍 Flattened for Search:", size=12,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                    ft.Text(flattened_preview, size=11,
                            color=ft.Colors.GREY_700, selectable=True),
                    ft.Divider(height=20, color=ft.Colors.GREY_300),
                ])

            self.full_text_container.content = ft.Column(
                cv_widgets,
                scroll=ft.ScrollMode.AUTO
            )

        self.full_text_container.update()

    def search_cvs(self, e=None):
        """🔍 SEARCH: Main search function using repository"""
        try:
            # Validate UI components are set
            if not all([self.keywords_input, self.algorithm_radio, self.top_matches_dropdown, self.similarity_slider]):
                self._show_message("❌ UI components not properly initialized")
                return

            # Get search parameters
            keywords = self.keywords_input.value.strip() if self.keywords_input.value else ""
            algorithm = self.algorithm_radio.value if self.algorithm_radio.value else "kmp"
            top_matches = int(
                self.top_matches_dropdown.value) if self.top_matches_dropdown.value else 10
            similarity_threshold = self.similarity_slider.value if self.similarity_slider.value else 0.3

            if not keywords:
                self._show_message("❌ Please enter keywords to search for")
                return

            # Show progress
            if self.progress_ring:
                self.progress_ring.visible = True
            self._show_message("🔍 Searching CVs...")

            # Clear previous results
            if self.results_container:
                self.results_container.controls.clear()  # Now works because it's a Column
            if self.summary_container:
                self.summary_container.controls.clear()   # Now works because it's a Column

            # Connect to repository
            if not self.repo.connect():
                self._show_message("❌ Failed to connect to database")
                return

            try:
                # Get database statistics
                stats = self.repo.get_cv_summary_statistics()

                if stats['total_cvs'] == 0:
                    self._show_message(
                        "❌ No CVs found in database. Please run seeding first!")
                    return

                # Perform search
                self._show_message(f"🔍 Searching {stats['total_cvs']} CVs...")

                search_results = self.repo.search_cvs_by_keywords(
                    keywords=keywords,
                    algorithm=algorithm,
                    top_matches=top_matches,
                    similarity_threshold=similarity_threshold
                )

                # Display results
                if search_results:
                    self._display_search_results(
                        search_results, keywords, stats)
                else:
                    self._show_message(
                        f"❌ No matches found for '{keywords}' in {stats['total_cvs']} CVs")

            finally:
                self.repo.disconnect()

        except Exception as e:
            self._show_message(f"❌ Search error: {str(e)}")
            print(f"Search error details: {e}")

        finally:
            if self.progress_ring:
                self.progress_ring.visible = False
            self.page.update()

    def _display_search_results(self, results, keywords: str, stats: dict):
        """📊 DISPLAY: Show search results"""
        try:
            # Update status
            self._show_message(
                f"✅ Found {len(results)} matches out of {stats['total_cvs']} CVs")

            # Show summary
            self._show_search_summary(results, keywords, stats)

            # Show individual results
            for i, result in enumerate(results, 1):
                self._create_result_card(result, i, keywords)

            self.page.update()

        except Exception as e:
            print(f"Error displaying results: {e}")
            self._show_message(f"❌ Error displaying results: {str(e)}")

    def _show_search_summary(self, results, keywords: str, stats: dict):
        """📈 SUMMARY: Show search summary"""
        try:
            if not self.summary_container:
                return

            # Role distribution in results
            role_counts = {}
            total_score = 0

            for result in results:
                role = result.application_detail.application_role
                role_counts[role] = role_counts.get(role, 0) + 1
                total_score += getattr(result, 'similarity_score', 0)

            avg_score = total_score / len(results) if results else 0

            # Create summary markdown
            summary_parts = [
                f"🎯 **Search Results for: '{keywords}'**",
                f"📊 Found **{len(results)}** matches out of **{stats['total_cvs']}** total CVs",
                f"⭐ Average similarity score: **{avg_score:.3f}**",
                "",
                "📈 **Results by Role:**"
            ]

            # Add role breakdown
            for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(results)) * 100
                summary_parts.append(
                    f"   • **{role}**: {count} matches ({percentage:.1f}%)")

            summary_text = "\n".join(summary_parts)

            # ✅ FIX: Access .controls on Column, not Container
            # Now works because summary_container is a Column
            self.summary_container.controls.clear()
            self.summary_container.controls.append(
                ft.Container(
                    content=ft.Markdown(
                        summary_text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=15,
                    margin=ft.margin.only(bottom=20)
                )
            )

        except Exception as e:
            print(f"Error creating summary: {e}")

    def _create_result_card(self, result, index: int, keywords: str):
        """🎴 CARD: Create result card for CV"""
        try:
            if not self.results_container:
                return

            profile = result.applicant_profile
            application = result.application_detail
            similarity = getattr(result, 'similarity_score', 0)
            matched_keywords = getattr(result, 'matched_keywords', [])

            # Create result card
            result_card = ft.Container(
                content=ft.Column([
                    # Header with rank and score
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                f"#{index}", weight=ft.FontWeight.BOLD, size=16),
                            bgcolor=ft.Colors.PRIMARY,
                            color=ft.Colors.WHITE,
                            border_radius=15,
                            padding=8,
                            width=40,
                            alignment=ft.alignment.center
                        ),
                        ft.Column([
                            ft.Text(
                                profile.full_name,
                                weight=ft.FontWeight.BOLD,
                                size=18
                            ),
                            ft.Text(
                                f"{application.application_role}",
                                color=ft.Colors.GREY_700,
                                size=14
                            )
                        ], expand=True),
                        ft.Container(
                            content=ft.Text(
                                f"{similarity:.3f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE
                            ),
                            bgcolor=ft.Colors.GREEN if similarity > 0.7 else ft.Colors.ORANGE if similarity > 0.4 else ft.Colors.RED,
                            border_radius=10,
                            padding=8,
                            alignment=ft.alignment.center
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    # Contact info
                    ft.Row([
                        ft.Icon(ft.icons.EMAIL, size=16,
                                color=ft.Colors.GREY_600),
                        ft.Text(profile.email, size=12),
                        ft.Icon(ft.icons.PHONE, size=16,
                                color=ft.Colors.GREY_600),
                        ft.Text(profile.phone_number or "N/A", size=12),
                    ], spacing=10),

                    # Matched keywords
                    ft.Row([
                        ft.Text("Matched keywords:",
                                weight=ft.FontWeight.BOLD, size=12),
                        ft.Text(
                            ", ".join(
                                matched_keywords) if matched_keywords else "None",
                            color=ft.Colors.GREEN_700,
                            size=12
                        )
                    ], spacing=10),

                    # Action buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "View Full CV",
                            icon=ft.icons.DESCRIPTION,
                            on_click=lambda e, res=result: self._show_cv_content(
                                res, keywords)
                        ),
                        ft.ElevatedButton(
                            "Highlight Keywords",
                            icon=ft.icons.HIGHLIGHT,
                            on_click=lambda e, res=result: self._show_cv_highlights(
                                res, keywords)
                        )
                    ], spacing=10)

                ], spacing=8),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                padding=15,
                margin=ft.margin.only(bottom=10)
            )

            # ✅ FIX: Access .controls on Column, not Container
            # Now works because results_container is a Column
            self.results_container.controls.append(result_card)

        except Exception as e:
            print(f"Error creating result card: {e}")

    def _show_cv_content(self, result, keywords: str):
        """📄 SHOW: Display full CV content"""
        try:
            if not self.full_text_container:
                return

            profile = result.applicant_profile
            cv_text = getattr(result, 'cv_text', '')

            if not cv_text:
                self._show_message("❌ CV text not available")
                return

            # ✅ FIX: Access .controls on Column, not Container
            # Now works because full_text_container is a Column
            self.full_text_container.controls.clear()

            # Create content display
            content = ft.Column([
                ft.Text(
                    f"📄 Full CV Content - {profile.full_name}",
                    weight=ft.FontWeight.BOLD,
                    size=18
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(
                        cv_text,
                        selectable=True,
                        size=12
                    ),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=5,
                    padding=15,
                    height=400,
                    scroll=ft.ScrollMode.AUTO
                )
            ])

            self.full_text_container.controls.append(content)
            self.page.update()

        except Exception as e:
            self._show_message(f"❌ Error displaying CV content: {str(e)}")

    def _show_cv_highlights(self, result, keywords: str):
        """🔍 HIGHLIGHT: Show highlighted keywords in CV"""
        try:
            if not self.highlights_container:
                return

            profile = result.applicant_profile
            cv_text = getattr(result, 'cv_text', '')

            if not cv_text:
                self._show_message("❌ CV text not available")
                return

            # ✅ FIX: Access .controls on Column, not Container
            # Now works because highlights_container is a Column
            self.highlights_container.controls.clear()

            # Highlight keywords using repository method
            highlighted_text = self.repo.get_highlighted_cv_text(
                cv_text, keywords.split())

            # Create highlights display
            content = ft.Column([
                ft.Text(
                    f"🔍 Highlighted Keywords - {profile.full_name}",
                    weight=ft.FontWeight.BOLD,
                    size=18
                ),
                ft.Text(
                    f"Keywords: {keywords}",
                    color=ft.Colors.GREY_700,
                    size=14
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Markdown(
                        highlighted_text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                    ),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=5,
                    padding=15,
                    height=400,
                    scroll=ft.ScrollMode.AUTO
                )
            ])

            self.highlights_container.controls.append(content)
            self.page.update()

        except Exception as e:
            self._show_message(f"❌ Error displaying highlights: {str(e)}")

    def _show_message(self, message: str):
        """💬 MESSAGE: Show message to user"""
        if self.status_text:
            self.status_text.value = message
            self.page.update()
        else:
            print(f"Message: {message}")

    def show_database_info(self, e=None):
        """📊 INFO: Show database information"""
        try:
            if not self.repo.connect():
                self._show_message("❌ Failed to connect to database")
                return

            stats = self.repo.get_cv_summary_statistics()
            self.repo.disconnect()

            if stats['total_cvs'] == 0:
                self._show_message(
                    "❌ No CVs found in database. Please run seeding first!")
                return

            if not self.summary_container:
                self._show_message(
                    f"📊 Database has {stats['total_cvs']} CVs across {stats['total_roles']} roles")
                return

            # Create info display
            info_parts = [
                f"📊 **Database Information**",
                f"Total CVs: **{stats['total_cvs']}**",
                f"Total Roles: **{stats['total_roles']}**",
                "",
                "📈 **CVs by Role:**"
            ]

            for role, count in stats['role_breakdown'].items():
                info_parts.append(f"   • **{role}**: {count} CVs")

            info_text = "\n".join(info_parts)

            # ✅ FIX: Access .controls on Column, not Container
            # Now works because summary_container is a Column
            self.summary_container.controls.clear()
            self.summary_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Markdown(
                            info_text,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                        ),
                        ft.ElevatedButton(
                            "Search Database CVs",
                            icon=ft.icons.SEARCH,
                            on_click=lambda e: self.keywords_input.focus() if self.keywords_input else None
                        )
                    ]),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    padding=15
                )
            )

            self.page.update()
            self._show_message(
                f"📊 Loaded database info: {stats['total_cvs']} CVs ready for search")

        except Exception as e:
            self._show_message(f"❌ Error getting database info: {str(e)}")
            print(f"Database info error: {e}")

    def search_cvs(self, e=None):
        """🔍 SEARCH: Main search function using repository"""
        try:
            # Validate UI components are set
            if not all([self.keywords_input, self.algorithm_radio, self.top_matches_dropdown, self.similarity_slider]):
                self._show_message("❌ UI components not properly initialized")
                return

            # Get search parameters
            keywords = self.keywords_input.value.strip() if self.keywords_input.value else ""
            algorithm = self.algorithm_radio.value if self.algorithm_radio.value else "kmp"
            top_matches = int(
                self.top_matches_dropdown.value) if self.top_matches_dropdown.value else 10
            similarity_threshold = self.similarity_slider.value if self.similarity_slider.value else 0.3

            if not keywords:
                self._show_message("❌ Please enter keywords to search for")
                return

            # Show progress
            if self.progress_ring:
                self.progress_ring.visible = True
            self._show_message("🔍 Searching CVs...")

            # ✅ FIX: Clear previous results using Column.controls
            if self.results_container:
                self.results_container.controls.clear()  # Now works because it's a Column
            if self.summary_container:
                self.summary_container.controls.clear()   # Now works because it's a Column

            # Connect to repository
            if not self.repo.connect():
                self._show_message("❌ Failed to connect to database")
                return

            try:
                # Get database statistics
                stats = self.repo.get_cv_summary_statistics()

                if stats['total_cvs'] == 0:
                    self._show_message(
                        "❌ No CVs found in database. Please run seeding first!")
                    return

                # Perform search
                self._show_message(f"🔍 Searching {stats['total_cvs']} CVs...")

                search_results = self.repo.search_cvs_by_keywords(
                    keywords=keywords,
                    algorithm=algorithm,
                    top_matches=top_matches,
                    similarity_threshold=similarity_threshold
                )

                # Display results
                if search_results:
                    self._display_search_results(
                        search_results, keywords, stats)
                else:
                    self._show_message(
                        f"❌ No matches found for '{keywords}' in {stats['total_cvs']} CVs")

            finally:
                self.repo.disconnect()

        except Exception as e:
            self._show_message(f"❌ Search error: {str(e)}")
            print(f"Search error details: {e}")

        finally:
            if self.progress_ring:
                self.progress_ring.visible = False
            self.page.update()


class SimpleUIHandlers:
    def __init__(self, page: ft.Page):
        """Initialize simple UI handlers"""
        self.page = page
        self.repo = CVRepository()

        # UI components
        self.keywords_input = None
        self.algorithm_radio = None
        self.results_text = None
        self.status_text = None
        self.progress_ring = None

    def create_components(self):
        """Create simple UI components"""
        # Keywords input
        self.keywords_input = ft.TextField(
            label="Enter keywords (comma-separated)",
            hint_text="e.g., python, javascript, sql",
            width=400
        )

        # Algorithm selection
        self.algorithm_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="kmp", label="KMP"),
                ft.Radio(value="bm", label="Boyer-Moore"),
                ft.Radio(value="regex", label="Regex")
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
            'results_text': self.results_text,
            'status_text': self.status_text,
            'progress_ring': self.progress_ring
        }

    def test_database_connection(self, e=None):
        """🔌 TEST: Database connection"""
        try:
            self.status_text.value = "Testing database connection..."
            self.status_text.color = ft.Colors.BLUE
            self.page.update()

            if self.repo.connect():
                stats = self.repo.get_statistics()
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

    def test_algorithms(self, e=None):
        """🧪 TEST: Your algorithms"""
        try:
            self.progress_ring.visible = True
            self.status_text.value = "Testing algorithms..."
            self.status_text.color = ft.Colors.BLUE
            self.page.update()

            if not self.repo.connect():
                self.status_text.value = "❌ Cannot connect to database"
                self.status_text.color = ft.Colors.RED
                self.progress_ring.visible = False
                self.page.update()
                return

            # Get a sample CV text
            all_cvs = self.repo.get_all_cvs()
            if not all_cvs:
                self.status_text.value = "❌ No CVs found for testing"
                self.status_text.color = ft.Colors.RED
                self.progress_ring.visible = False
                self.repo.disconnect()
                self.page.update()
                return

            # Use first CV for testing
            sample_cv = all_cvs[0]
            test_pattern = "python"  # Test pattern

            # Test algorithms manually since test_algorithms might not exist
            result_text = f"ALGORITHM TEST RESULTS (Pattern: '{test_pattern}'):\n\n"
            result_text += f"Test CV: {sample_cv.applicant_profile.full_name}\n"
            result_text += f"CV Text Length: {len(sample_cv.cv_text)} characters\n\n"

            # Test your string matcher directly
            from algorithms.string_matcher import StringMatcher
            matcher = StringMatcher()

            # Test KMP
            start_time = time.time()
            try:
                kmp_matches = matcher.kmp_search(
                    sample_cv.cv_text.lower(), test_pattern)
                kmp_time = time.time() - start_time
                result_text += f"KMP Algorithm:\n"
                result_text += f"  • Matches found: {len(kmp_matches) if kmp_matches else 0}\n"
                result_text += f"  • Time: {kmp_time:.6f} seconds\n"
                result_text += f"  • First positions: {kmp_matches[:5] if kmp_matches else 'None'}\n\n"
            except Exception as e:
                result_text += f"KMP Algorithm: Error - {str(e)}\n\n"

            # Test Boyer-Moore
            start_time = time.time()
            try:
                bm_matches = matcher.boyer_moore_search(
                    sample_cv.cv_text.lower(), test_pattern)
                bm_time = time.time() - start_time
                result_text += f"Boyer-Moore Algorithm:\n"
                result_text += f"  • Matches found: {len(bm_matches) if bm_matches else 0}\n"
                result_text += f"  • Time: {bm_time:.6f} seconds\n"
                result_text += f"  • First positions: {bm_matches[:5] if bm_matches else 'None'}\n\n"
            except Exception as e:
                result_text += f"Boyer-Moore Algorithm: Error - {str(e)}\n\n"

            # Test Levenshtein
            start_time = time.time()
            try:
                words = sample_cv.cv_text.split()[:50]  # First 50 words
                similarities = []
                for word in words:
                    if len(word) >= 3:
                        sim = matcher.calculate_similarity(
                            test_pattern, word.lower())
                        if sim > 70:
                            similarities.append((word, sim))

                lev_time = time.time() - start_time
                result_text += f"Levenshtein Distance:\n"
                result_text += f"  • High similarities (>70%): {len(similarities)}\n"
                result_text += f"  • Time: {lev_time:.6f} seconds\n"
                result_text += f"  • Top matches: {sorted(similarities, key=lambda x: x[1], reverse=True)[:3]}\n\n"
            except Exception as e:
                result_text += f"Levenshtein Distance: Error - {str(e)}\n\n"

            self.repo.disconnect()

            self.results_text.value = result_text
            self.status_text.value = "✅ Algorithm test completed"
            self.status_text.color = ft.Colors.GREEN

        except Exception as e:
            self.results_text.value = f"Algorithm test error: {str(e)}"
            self.status_text.value = f"❌ Test failed: {str(e)}"
            self.status_text.color = ft.Colors.RED

        finally:
            self.progress_ring.visible = False
            self.page.update()

    def search_cvs(self, e=None):
        """🔍 SEARCH: Test search functionality"""
        try:
            keywords = self.keywords_input.value.strip() if self.keywords_input.value else ""
            algorithm = self.algorithm_radio.value if self.algorithm_radio.value else "kmp"

            if not keywords:
                self.status_text.value = "❌ Please enter keywords"
                self.status_text.color = ft.Colors.RED
                self.page.update()
                return

            self.progress_ring.visible = True
            self.status_text.value = f"Searching with {algorithm.upper()}..."
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
                top_matches=10,
                similarity_threshold=0.3
            )
            search_time = time.time() - search_start

            self.repo.disconnect()

            # Display results
            result_text = f"SEARCH RESULTS for '{keywords}' using {algorithm.upper()}:\n\n"
            result_text += f"Search Time: {search_time:.3f} seconds\n"
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
                    result_text += f"   Matched: {', '.join(matched_kw)}\n"
                    result_text += f"   Email: {profile.email}\n\n"
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
        """🗑️ CLEAR: Clear all results"""
        self.results_text.value = "Results cleared."
        self.keywords_input.value = ""
        self.status_text.value = "Ready"
        self.status_text.color = ft.Colors.GREEN
        self.page.update()
