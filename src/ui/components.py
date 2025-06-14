import flet as ft


class UIComponents:
    @staticmethod
    def create_header():
        """Create header section - CV ATS Title"""
        return ft.Column([
            ft.Text("CV ATS - Applicant Tracking System",
                    size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Advanced PDF CV Parser with KMP & Boyer-Moore + Levenshtein Distance",
                    size=14, color=ft.Colors.GREY_600),
            ft.Divider(),
        ])

    @staticmethod
    def create_file_selection_section(pick_files_callback, selected_files_text):
        """Create file selection section"""
        return ft.Column([
            ft.Text("1. Select PDF Files", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.ElevatedButton(
                    "Select PDF Files",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=pick_files_callback,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    )
                ),
                selected_files_text
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(),
        ])

    @staticmethod
    def create_search_configuration(algorithm_radio, keywords_input, top_matches_dropdown, similarity_text, similarity_slider, search_callback, clear_callback):
        """Create search configuration section with all required components"""
        return ft.Column([
            ft.Text("2. Configure Search", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Algorithm Selection:", size=14,
                                weight=ft.FontWeight.BOLD),
                        algorithm_radio
                    ]),
                    expand=1
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Keywords:", size=14,
                                weight=ft.FontWeight.BOLD),
                        keywords_input
                    ]),
                    expand=2
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Top Matches:", size=14,
                                weight=ft.FontWeight.BOLD),
                        top_matches_dropdown
                    ]),
                    expand=1
                )
            ]),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        similarity_text,
                        similarity_slider
                    ]),
                    expand=2
                ),
                ft.Container(
                    content=ft.Column([
                        ft.ElevatedButton(
                            "Start Search",
                            icon=ft.Icons.SEARCH,
                            on_click=search_callback,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.GREEN_600
                            )
                        ),
                        ft.ElevatedButton(
                            "Clear All",
                            icon=ft.Icons.CLEAR,
                            on_click=clear_callback,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.RED_600
                            )
                        )
                    ]),
                    expand=1
                )
            ]),
            ft.Divider(),
        ])

    @staticmethod
    def create_summary_section(summary_container):
        """Create summary result section - REQUIRED BY SPEC"""
        return ft.Column([
            ft.Text("3. Summary Result Section",
                    size=18, weight=ft.FontWeight.BOLD),
            summary_container,
            ft.Divider(),
        ])

    @staticmethod
    def create_results_section(progress_ring, status_text, results_container):
        """Create results section with search results"""
        return ft.Column([
            ft.Row([
                ft.Text("4. Search Results", size=18,
                        weight=ft.FontWeight.BOLD),
                progress_ring,
                status_text
            ]),
            results_container,
            ft.Divider(),
        ])

    @staticmethod
    def create_content_display_section(full_text_container, highlights_container):
        """Create content display section with CV content and summary"""
        return ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("5. Full CV Content", size=16,
                            weight=ft.FontWeight.BOLD),
                    full_text_container
                ]),
                expand=1
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("6. CV Summary / Highlights",
                            size=16, weight=ft.FontWeight.BOLD),
                    highlights_container
                ]),
                expand=1
            )
        ])

    @staticmethod
    def create_container(width=1200, height=800):
        """Create main container"""
        return ft.Container(
            content=ft.Column([], spacing=15),
            padding=20,
            expand=True
        )
        
    @staticmethod
    def create_database_section(on_show_db_info):
        """Create database information section"""
        return ft.Container(
            content=ft.Column([
                ft.Text("📊 Database Search", weight=ft.FontWeight.BOLD, size=16),
                ft.Text(
                    "Search keywords in CVs already stored in the database (from seeding process)",
                    color=ft.colors.GREY_700,
                    size=12
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Show Database Info",
                        icon=ft.icons.INFO,
                        on_click=on_show_db_info
                    ),
                    ft.Text(
                        "💡 No need to upload files - search existing CVs!",
                        color=ft.colors.BLUE_700,
                        size=12,
                        italic=True
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=8),
            bgcolor=ft.colors.BLUE_50,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=15)
        )
    
    @staticmethod
    def create_encryption_status_section(encryption_enabled=False, on_manage_encryption=None):
        """Create encryption status section"""
        if encryption_enabled:
            status_color = ft.colors.GREEN_50
            status_icon = ft.icons.SECURITY
            status_text = "🔒 Encryption Active"
            status_desc = "Personal data is automatically encrypted in the database"
            button_text = "Manage Encryption"
        else:
            status_color = ft.colors.ORANGE_50
            status_icon = ft.icons.SECURITY_UPDATE_WARNING
            status_text = "📝 Standard Mode"
            status_desc = "Data stored in plaintext (demo mode)"
            button_text = "Enable Encryption"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(status_icon, color=ft.colors.BLUE_700),
                    ft.Text(status_text, weight=ft.FontWeight.BOLD, size=14),
                    ft.Spacer(),
                    ft.ElevatedButton(
                        button_text,
                        icon=ft.icons.SETTINGS,
                        on_click=on_manage_encryption,
                        scale=0.9
                    ) if on_manage_encryption else ft.Container()
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(
                    status_desc,
                    color=ft.colors.GREY_700,
                    size=12
                )
            ], spacing=4),
            bgcolor=status_color,
            padding=ft.padding.all(12),
            border_radius=8,
            margin=ft.margin.only(bottom=10)
        )