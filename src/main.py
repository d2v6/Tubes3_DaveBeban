import flet as ft
from ui.components import UIComponents
from ui.handlers import UIHandlers

def main(page: ft.Page):
    page.title = "CV Matching System - DaveBeban"
    page.window.width = 1200
    page.window.height = 800
    page.scroll = ft.ScrollMode.AUTO
    
    # Initialize handlers
    handlers = UIHandlers()
    
    # Create file picker
    file_picker = handlers.create_file_picker(page)
    
    # Setup UI components
    components = handlers.setup_ui_components()
    
    # Create main layout
    page.add(
        ft.Container(
            content=ft.Column([
                # Header
                UIComponents.create_header(),
                
                # File selection section
                UIComponents.create_file_selection_section(
                    lambda e: handlers.pick_files(e, file_picker),
                    components['selected_files_text']
                ),
                
                # Search configuration section
                UIComponents.create_search_configuration(
                    components['algorithm_radio'],
                    components['keywords_input'],
                    components['similarity_text'],
                    components['similarity_slider'],
                    handlers.search_cvs,
                    handlers.clear_all
                ),
                
                # Results section
                UIComponents.create_results_section(
                    components['progress_ring'],
                    components['status_text'],
                    components['results_container']
                ),
                
                # Content display section
                UIComponents.create_content_display_section(
                    components['full_text_container'],
                    components['highlights_container']
                )
                
            ], spacing=15),
            padding=20,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(main)