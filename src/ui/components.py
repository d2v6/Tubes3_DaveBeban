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
    def create_results_section(progress_ring, status_text, results_container):
        """Create results section with search results"""
        return ft.Column([
            ft.Row([
                ft.Text("Search Results", size=18,
                        weight=ft.FontWeight.BOLD),
                progress_ring,
                status_text
            ]),
            results_container,
            ft.Divider(),
        ])

    @staticmethod
    def create_container(width=1200, height=800):
        """Create main container"""
        return ft.Container(
            content=ft.Column([], spacing=15),
            padding=20,
            expand=True
        )
