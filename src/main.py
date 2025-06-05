import flet as ft
from ui.handlers import SimpleUIHandlers


def main(page: ft.Page):
    """🚀 SIMPLE MAIN: Test your algorithms and database connection"""

    # Configure page
    page.title = "CV ATS - Algorithm & Database Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 900
    page.window_height = 700

    # Initialize handlers
    handlers = SimpleUIHandlers(page)
    components = handlers.create_components()

    # Create simple UI
    page.add(
        ft.Column([
            # Header
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "🧪 CV ATS - Algorithm & Database Test",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700
                    ),
                    ft.Text(
                        "Simple UI to test your string matching algorithms and database connection",
                        size=14,
                        color=ft.Colors.GREY_700
                    ),
                ]),
                margin=ft.margin.only(bottom=20)
            ),

            # Database Test Section
            ft.Container(
                content=ft.Column([
                    ft.Text("🔌 Database Connection Test",
                            size=18, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Test Database Connection",
                        icon=ft.icons.STORAGE,
                        on_click=handlers.test_database_connection,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                    )
                ]),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                padding=15,
                margin=ft.margin.only(bottom=15)
            ),

            # Algorithm Test Section
            ft.Container(
                content=ft.Column([
                    ft.Text("🧪 Algorithm Test", size=18,
                            weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Test Your Algorithms (KMP, Boyer-Moore, Levenshtein)",
                        icon=ft.icons.SCIENCE,
                        on_click=handlers.test_algorithms,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
                    )
                ]),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=10,
                padding=15,
                margin=ft.margin.only(bottom=15)
            ),

            # Search Test Section
            ft.Container(
                content=ft.Column([
                    ft.Text("🔍 Search Test", size=18,
                            weight=ft.FontWeight.BOLD),

                    # Keywords input
                    components['keywords_input'],

                    # Algorithm selection
                    ft.Text("Algorithm:", weight=ft.FontWeight.BOLD, size=14),
                    components['algorithm_radio'],

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

            # Status Section
            ft.Container(
                content=ft.Row([
                    ft.Text("Status:", weight=ft.FontWeight.BOLD),
                    components['progress_ring'],
                    components['status_text']
                ], spacing=10),
                padding=10
            ),

            # Results Section
            ft.Container(
                content=ft.Column([
                    ft.Text("📊 Results", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column([
                            components['results_text']
                        ], scroll=ft.ScrollMode.AUTO),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=5,
                        padding=15,
                        height=250
                    )
                ]),
                margin=ft.margin.only(top=10)
            )

        ], spacing=0, scroll=ft.ScrollMode.AUTO)
    )


# Run the app
if __name__ == "__main__":
    ft.app(target=main)
