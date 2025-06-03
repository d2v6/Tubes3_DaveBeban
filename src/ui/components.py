import flet as ft

class UIComponents:
    @staticmethod
    def create_header():
        """Create header section"""
        return ft.Column([
            ft.Text("CV Matching System", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Advanced PDF CV Parser with KMP & Boyer-Moore Algorithms", 
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
    def create_search_configuration(algorithm_radio, keywords_input, similarity_text, similarity_slider, search_callback, clear_callback):
        """Create search configuration section"""
        return ft.Column([
            ft.Text("2. Configure Search", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Algorithm Selection:", size=14, weight=ft.FontWeight.BOLD),
                        algorithm_radio
                    ]),
                    expand=1
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Keywords:", size=14, weight=ft.FontWeight.BOLD),
                        keywords_input
                    ]),
                    expand=2
                )
            ]),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        similarity_text,
                        similarity_slider
                    ]),
                    expand=1
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
    def create_results_section(progress_ring, status_text, results_container):
        """Create results section"""
        return ft.Column([
            ft.Row([
                ft.Text("3. Search Results", size=18, weight=ft.FontWeight.BOLD),
                progress_ring,
                status_text
            ]),
            results_container,
            ft.Divider(),
        ])
    
    @staticmethod
    def create_content_display_section(full_text_container, highlights_container):
        """Create content display section"""
        return ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("4. Full CV Content", size=16, weight=ft.FontWeight.BOLD),
                    full_text_container
                ]),
                expand=1
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("5. Search Highlights", size=16, weight=ft.FontWeight.BOLD),
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