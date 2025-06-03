import os
from typing import List

class FileHandler:
    @staticmethod
    def save_parsed_text(text: str, filename: str, output_dir: str = "output"):
        """Save parsed text to file"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_filename = f"{os.path.splitext(filename)[0]}_parsed.txt"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Parsed text saved to: {output_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
    
    @staticmethod
    def highlight_text_with_keywords(text: str, keywords: List[str]) -> str:
        """Highlight keywords in text with context"""
        highlighted_sections = []
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_clean = keyword.split(" (~")[0]
            keyword_lower = keyword_clean.lower()
            
            start = 0
            while True:
                pos = text_lower.find(keyword_lower, start)
                if pos == -1:
                    break
                
                context_start = max(0, pos - 50)
                context_end = min(len(text), pos + len(keyword_clean) + 50)
                
                context = text[context_start:context_end]
                
                keyword_in_context = text[pos:pos + len(keyword_clean)]
                highlighted_context = context.replace(
                    keyword_in_context, 
                    f"**{keyword_in_context}**"
                )
                
                highlighted_sections.append(f"...{highlighted_context}...")
                start = pos + 1
        
        return "\n\n".join(highlighted_sections)