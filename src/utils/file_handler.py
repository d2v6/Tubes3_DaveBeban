import os
import re
from typing import List

class FileHandler:
    @staticmethod
    def save_parsed_text(text: str, filename: str, output_dir: str = "output") -> str:
        """Save parsed text to file with enhanced error handling"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Simple but effective filename sanitization
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            output_filename = f"{os.path.splitext(safe_filename)[0]}_parsed.txt"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Parsed text saved to: {output_path}")
            return output_path
        except PermissionError:
            print(f"Permission denied: Cannot write to {output_dir}")
            return ""
        except Exception as e:
            print(f"Error saving file: {e}")
            return ""

    @staticmethod
    def highlight_text_with_keywords(text: str, keywords: List[str]) -> str:
        """
        Highlight keywords in text with improved context and deduplication
        """
        if not text or not keywords:
            return "No text or keywords provided"
        
        highlighted_sections = []
        text_lower = text.lower()
        seen_positions = set()  # Simple deduplication
        
        for keyword in keywords:
            # Clean keyword (remove similarity info)
            keyword_clean = re.sub(r'\s*\(~.*?\)', '', keyword).strip().lower()
            if not keyword_clean or len(keyword_clean) < 2:
                continue
            
            # Use regex for better word boundary matching
            pattern = r'\b' + re.escape(keyword_clean) + r'\b'
            
            for match in re.finditer(pattern, text_lower):
                pos = match.start()
                
                # Skip if we've already highlighted this area
                if any(abs(pos - seen_pos) < 30 for seen_pos in seen_positions):
                    continue
                seen_positions.add(pos)
                
                # Dynamic context size (longer keywords get more context)
                context_size = max(60, min(120, len(keyword_clean) * 8))
                context_start = max(0, pos - context_size)
                context_end = min(len(text), pos + len(keyword_clean) + context_size)
                
                # Extract and highlight context
                context = text[context_start:context_end]
                
                # Case-insensitive highlighting while preserving original case
                highlighted_context = re.sub(
                    pattern,
                    lambda m: f"**{m.group(0).upper()}**",
                    context,
                    flags=re.IGNORECASE
                )
                
                highlighted_sections.append(f"...{highlighted_context}...")
        
        if not highlighted_sections:
            return "No keyword matches found"
        
        return "\n\n".join(highlighted_sections)

    @staticmethod
    def save_search_results(results: List[dict], output_dir: str = "output") -> str:
        """Save search results summary to file"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"search_results_{timestamp}.txt")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("CV ATS Search Results Summary\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Results: {len(results)}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"Result #{i}:\n")
                    f.write(f"  Filename: {result.get('filename', 'Unknown')}\n")
                    f.write(f"  Similarity: {result.get('similarity', 0):.1f}%\n")
                    f.write(f"  Matches: {result.get('total_matches', 0)}\n")
                    f.write(f"  Keywords: {', '.join(result.get('keywords', []))}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"Search results saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving search results: {e}")
            return ""