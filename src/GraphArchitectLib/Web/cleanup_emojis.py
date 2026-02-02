"""
Script to remove emojis from Python files and logs.
"""
import re
import os
from pathlib import Path

# Common emoji patterns
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # miscellaneous symbols
    "]+",
    flags=re.UNICODE
)

def remove_emojis_from_string(text: str) -> str:
    """Remove all emojis from string."""
    return EMOJI_PATTERN.sub('', text)

def process_file(file_path: Path) -> tuple[int, int]:
    """
    Process single Python file to remove emojis.
    
    Returns:
        Tuple of (lines_modified, emojis_removed)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Remove emojis
        cleaned_content = remove_emojis_from_string(original_content)
        
        # Count changes
        lines_modified = 0
        emojis_removed = 0
        
        if original_content != cleaned_content:
            original_lines = original_content.split('\n')
            cleaned_lines = cleaned_content.split('\n')
            
            for orig, clean in zip(original_lines, cleaned_lines):
                if orig != clean:
                    lines_modified += 1
                    emojis_removed += len(orig) - len(clean)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"  Modified: {file_path.name} ({lines_modified} lines, {emojis_removed} chars)")
        
        return lines_modified, emojis_removed
        
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return 0, 0

def main():
    """Process all Python files in Web directory."""
    web_dir = Path(__file__).parent
    
    print("Removing emojis from Python files...")
    print(f"Directory: {web_dir}")
    print("-" * 60)
    
    total_files = 0
    total_lines = 0
    total_emojis = 0
    
    # Process all .py files
    for py_file in web_dir.glob("*.py"):
        if py_file.name == "cleanup_emojis.py":
            continue  # Skip this script
        
        lines, emojis = process_file(py_file)
        if lines > 0:
            total_files += 1
            total_lines += lines
            total_emojis += emojis
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  Files modified: {total_files}")
    print(f"  Lines modified: {total_lines}")
    print(f"  Emojis removed: {total_emojis}")
    print("-" * 60)
    print("Done!")

if __name__ == "__main__":
    main()
