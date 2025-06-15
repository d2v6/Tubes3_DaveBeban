from ui.components import UIComponents
from ui.handlers import UIHandlers
import flet as ft
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main(page: ft.Page):
    page.title = "DAVEBEBAN CV ATS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 1000
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

    # Initialize handlers
    handlers = UIHandlers(page)
    components = handlers.create_components()

    page.add(
        ft.Column([
            # Header
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "DAVEBEBAN CV ATS",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700
                    ),
                ]),
                margin=ft.margin.only(bottom=20)
            ),

            ft.Container(
                content=ft.Row([
                    # Database Test Section
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Load CVs from Database",
                                    size=18, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton(
                                "Load CVs",
                                icon=ft.icons.STORAGE,
                                on_click=handlers.test_database_connection_and_load,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                            )
                        ]),
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        padding=15,
                        margin=ft.margin.only(bottom=15)
                    ),
                ])
            ),

            # Search Test Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Search Test", size=18,
                            weight=ft.FontWeight.BOLD),

                    # Keywords input
                    components['keywords_input'],

                    # Search parameters row
                    ft.Row([
                        # Algorithm selection
                        ft.Column([
                            ft.Text("Algorithm:",
                                    weight=ft.FontWeight.BOLD, size=14),
                            components['algorithm_radio']
                        ]),

                        # Top matches input
                        ft.Column([
                            ft.Text("Top Matches:",
                                    weight=ft.FontWeight.BOLD, size=14),
                            components['top_matches_input']
                        ])
                    ], spacing=20),

                    # Search buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "Search CVs",
                            icon=ft.icons.SEARCH,
                            on_click=handlers.search_cvs,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE)
                        ),
                        ft.ElevatedButton(
                            "Clear Results",
                            icon=ft.icons.CLEAR,
                            on_click=handlers.clear_results,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
                        )
                    ], spacing=10)
                ]),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=10,
                padding=15,
                margin=ft.margin.only(bottom=15)
            ),

            # Results Section
            UIComponents.create_results_section(
                components['progress_ring'],
                components['status_text'],
                components['results_container']
            )
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    )


# Run the app
if __name__ == "__main__":
    ft.app(target=main)
