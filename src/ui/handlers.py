import flet as ft
import os
import sys
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cv_match import CVMatch
from algorithms.string_matcher import StringMatcher
from utils.pdf_parser import PDFParser
from utils.file_handler import FileHandler

class UIHandlers:
    def __init__(self):
        self.parsed_cvs: Dict[str, str] = {}
        self.search_results: List[CVMatch] = []
    
    def create_file_picker(self, page: ft.Page):
        """Create and setup file picker"""
        file_picker = ft.FilePicker(
            on_result=self.handle_file_selection
        )
        page.overlay.append(file_picker)
        return file_picker
    
    def setup_ui_components(self):
        """Setup all UI components"""
        # Algorithm selection
        algorithm_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="kmp", label="Knuth-Morris-Pratt (KMP)"),
                ft.Radio(value="boyer_moore", label="Boyer-Moore")
            ]),
            value="kmp"
        )
        
        # Keywords input
        keywords_input = ft.TextField(
            label="Enter keywords (comma-separated)",
            hint_text="e.g., python, machine learning, data science",
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=400
        )
        
        # Similarity threshold
        similarity_slider = ft.Slider(
            min=0,
            max=100,
            divisions=20,
            value=70,
            label="Similarity Threshold: {value}%",
            width=300
        )
        
        similarity_text = ft.Text("Similarity Threshold: 70%", size=14)
        
        def update_similarity_text(e):
            similarity_text.value = f"Similarity Threshold: {int(similarity_slider.value)}%"
            similarity_text.update()
        
        similarity_slider.on_change = update_similarity_text
        
        selected_files_text = ft.Text("No files selected", size=14, color=ft.Colors.GREY_600)
        
        results_container = ft.Container(
            content=ft.Column([
                ft.Text("Search results will appear here...", size=12)
            ], scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=200,
            expand=True
        )
        
        full_text_container = ft.Container(
            content=ft.Column([
                ft.Text("Full CV content will appear here...", size=12)
            ], scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=300,
            expand=True
        )
        
        highlights_container = ft.Container(
            content=ft.Column([
                ft.Text("Highlighted search terms will appear here...", size=12)
            ], scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=10,
            height=200,
            expand=True
        )
        
        progress_ring = ft.ProgressRing(visible=False)
        status_text = ft.Text("", size=12, color=ft.Colors.BLUE_600)
        
        self.algorithm_radio = algorithm_radio
        self.keywords_input = keywords_input
        self.similarity_slider = similarity_slider
        self.similarity_text = similarity_text
        self.selected_files_text = selected_files_text
        self.results_container = results_container
        self.full_text_container = full_text_container
        self.highlights_container = highlights_container
        self.progress_ring = progress_ring
        self.status_text = status_text
        
        return {
            'algorithm_radio': algorithm_radio,
            'keywords_input': keywords_input,
            'similarity_slider': similarity_slider,
            'similarity_text': similarity_text,
            'selected_files_text': selected_files_text,
            'results_container': results_container,
            'full_text_container': full_text_container,
            'highlights_container': highlights_container,
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
        """Handle file selection"""
        if e.files:
            self.selected_files_text.value = f"Selected {len(e.files)} PDF file(s)"
            self.selected_files_text.color = ft.Colors.GREEN_600
            self.selected_files_text.update()
            
            self.progress_ring.visible = True
            self.status_text.value = "Parsing PDF files..."
            self.status_text.update()
            
            self.parsed_cvs.clear()
            for file in e.files:
                file_path = file.path
                filename = os.path.basename(file_path)
                parsed_text = PDFParser.parse_pdf(file_path)
                if parsed_text:
                    self.parsed_cvs[filename] = parsed_text
                    FileHandler.save_parsed_text(parsed_text, filename)
            
            self.display_all_cvs()
            
            self.progress_ring.visible = False
            self.status_text.value = f"Successfully parsed {len(self.parsed_cvs)} CV(s)"
            self.status_text.update()
        else:
            self.selected_files_text.value = "No files selected"
            self.selected_files_text.color = ft.Colors.GREY_600
            self.selected_files_text.update()
    
    def display_all_cvs(self):
        """Display all parsed CV content immediately"""
        if not self.parsed_cvs:
            self.full_text_container.content = ft.Column([
                ft.Text("Full CV content will appear here...", size=12)
            ], scroll=ft.ScrollMode.AUTO)
        else:
            cv_widgets = []
            for i, (filename, content) in enumerate(self.parsed_cvs.items(), 1):
                cv_widgets.extend([
                    ft.Text(f"CV #{i}: {filename}", 
                           size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600),
                    ft.Divider(),
                    ft.Text(content, size=12, selectable=True),
                    ft.Divider(height=20, color=ft.Colors.GREY_300),
                ])
            
            self.full_text_container.content = ft.Column(
                cv_widgets,
                scroll=ft.ScrollMode.AUTO
            )
        
        self.full_text_container.update()
    
    def search_cvs(self, e):
        """Handle search CVs"""
        if not self.parsed_cvs:
            self.status_text.value = "Please select and parse PDF files first"
            self.status_text.color = ft.Colors.RED_600
            self.status_text.update()
            return
        
        if not self.keywords_input.value.strip():
            self.status_text.value = "Please enter keywords to search"
            self.status_text.color = ft.Colors.RED_600
            self.status_text.update()
            return
        
        self.progress_ring.visible = True
        self.status_text.value = "Searching CVs..."
        self.status_text.color = ft.Colors.BLUE_600
        self.status_text.update()
        
        keywords = [kw.strip().lower() for kw in self.keywords_input.value.split(',') if kw.strip()]
        algorithm = self.algorithm_radio.value
        threshold = self.similarity_slider.value
        
        self.search_results.clear()
        matcher = StringMatcher()
        
        for filename, cv_text in self.parsed_cvs.items():
            matched_keywords = []
            
            for keyword in keywords:
                if algorithm == "kmp":
                    matches = matcher.kmp_search(cv_text, keyword)
                else:
                    matches = matcher.boyer_moore_search(cv_text, keyword)
                
                if matches:
                    matched_keywords.append(keyword)
                else:
                    words = cv_text.lower().split()
                    for word in words:
                        similarity = matcher.calculate_similarity(keyword, word)
                        if similarity >= threshold:
                            matched_keywords.append(f"{keyword} (~{similarity:.1f}% similar to '{word}')")
                            break
            
            if matched_keywords:
                similarity_score = (len(matched_keywords) / len(keywords)) * 100
                
                cv_match = CVMatch(
                    filename=filename,
                    similarity_score=similarity_score,
                    matched_keywords=matched_keywords,
                    algorithm_used=algorithm.upper(),
                    full_text=cv_text
                )
                self.search_results.append(cv_match)
        
        self.search_results.sort(key=lambda x: x.similarity_score, reverse=True)
        self.display_results()
        
        self.progress_ring.visible = False
        self.status_text.value = f"Search completed. Found {len(self.search_results)} matching CV(s)"
        self.status_text.color = ft.Colors.GREEN_600
        self.status_text.update()
    
    def show_cv_highlights(self, cv_match: CVMatch):
        """Display highlights for selected CV"""
        highlighted_text = FileHandler.highlight_text_with_keywords(cv_match.full_text, cv_match.matched_keywords)
        
        self.highlights_container.content = ft.Column([
            ft.Text(f"Search Highlights - {cv_match.filename}", 
                   size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
            ft.Text(f"Keywords found: {', '.join(cv_match.matched_keywords)}", 
                   size=12, color=ft.Colors.GREY_700),
            ft.Divider(),
            ft.Text(highlighted_text if highlighted_text else "No highlights found", 
                   size=12, selectable=True)
        ], scroll=ft.ScrollMode.AUTO)
        
        self.highlights_container.update()
    
    def display_results(self):
        """Display search results"""
        results_widgets = []
        
        if not self.search_results:
            results_widgets.append(
                ft.Text("No matching CVs found", size=14, color=ft.Colors.GREY_600)
            )
        else:
            for i, result in enumerate(self.search_results, 1):
                result_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"#{i}. {result.filename}", 
                                        size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{result.similarity_score:.1f}%", 
                                        size=14, color=ft.Colors.GREEN_600)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"Algorithm: {result.algorithm_used}", 
                                    size=12, color=ft.Colors.BLUE_600),
                            ft.Text("Matched Keywords:", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(", ".join(result.matched_keywords), 
                                   size=12, color=ft.Colors.GREY_700),
                            ft.ElevatedButton(
                                "Show Highlights",
                                icon=ft.Icons.HIGHLIGHT,
                                on_click=lambda e, cv=result: self.show_cv_highlights(cv),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.PURPLE_600
                                )
                            )
                        ], spacing=5),
                        padding=10
                    ),
                    elevation=2
                )
                results_widgets.append(result_card)
        
        self.results_container.content = ft.Column(
            results_widgets,
            scroll=ft.ScrollMode.AUTO,
            spacing=10
        )
        self.results_container.update()
    
    def clear_all(self, e):
        """Clear all data and UI"""
        self.parsed_cvs.clear()
        self.search_results.clear()
        self.selected_files_text.value = "No files selected"
        self.selected_files_text.color = ft.Colors.GREY_600
        self.keywords_input.value = ""
        self.status_text.value = ""
        
        self.results_container.content = ft.Column([
            ft.Text("Search results will appear here...", size=12)
        ])
        self.full_text_container.content = ft.Column([
            ft.Text("Full CV content will appear here...", size=12)
        ])
        self.highlights_container.content = ft.Column([
            ft.Text("Highlighted search terms will appear here...", size=12)
        ])
        
        self.selected_files_text.update()
        self.keywords_input.update()
        self.status_text.update()
        self.results_container.update()
        self.full_text_container.update()
        self.highlights_container.update()