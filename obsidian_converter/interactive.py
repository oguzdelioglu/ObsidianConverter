"""
Interactive mode for ObsidianConverter
"""
import os
import re
import sys
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path

logger = logging.getLogger("obsidian_converter")


class InteractiveReviewer:
    """Interactive review and edit mode for generated notes"""
    
    def __init__(self, editor=None):
        """
        Initialize the interactive reviewer
        
        Args:
            editor: Text editor to use (defaults to environment variable EDITOR)
        """
        self.editor = editor or os.environ.get("EDITOR", self._get_default_editor())
        if not self.editor:
            logger.warning("No text editor found for interactive mode. Using basic console editing.")
    
    def _get_default_editor(self):
        """Find a default editor based on the platform"""
        if sys.platform.startswith('win'):
            return "notepad.exe"
        elif sys.platform.startswith('darwin'):
            return "open -e"  # TextEdit on macOS
        else:
            # Try to find common editors on Linux
            for editor in ["nano", "vim", "vi", "emacs", "gedit"]:
                if self._command_exists(editor):
                    return editor
        return None
    
    def _command_exists(self, cmd):
        """Check if a command exists in the system path"""
        return shutil.which(cmd) is not None
    
    def review_note(self, title, content, category=None):
        """
        Review and edit a note before saving
        
        Args:
            title: Note title
            content: Note content
            category: Note category
            
        Returns:
            Tuple of (modified_content, save_flag, category)
            - modified_content: The potentially modified content
            - save_flag: Whether to save the note (True) or discard it (False)
            - category: Potentially modified category
        """
        print("\n" + "=" * 60)
        print(f"Reviewing note: {title}")
        if category:
            print(f"Category: {category}")
        print("=" * 60)
        
        print("\nPreview:")
        print("-" * 40)
        
        # Print preview (first few lines)
        preview_lines = content.split('\n')[:15]  # Show first 15 lines
        for line in preview_lines:
            print(line)
        
        if len(content.split('\n')) > 15:
            print("...")
            print(f"[Note content truncated, full note has {len(content.split())} words]")
        
        print("-" * 40)
        
        # Ask for action
        while True:
            action = input("\nActions: [e]dit, [s]ave, [d]iscard, [c]hange category, [v]iew full: ").lower()
            
            if action.startswith('e'):
                # Edit the note
                modified_content = self._edit_content(content)
                return modified_content, True, category
            
            elif action.startswith('s'):
                # Save as is
                return content, True, category
            
            elif action.startswith('d'):
                # Discard the note
                confirm = input("Are you sure you want to discard this note? (y/n): ").lower()
                if confirm.startswith('y'):
                    return content, False, category
            
            elif action.startswith('c'):
                # Change category
                new_category = input(f"Enter new category (current: {category or 'None'}): ")
                if new_category.strip():
                    category = new_category.strip()
                return content, True, category
            
            elif action.startswith('v'):
                # View full content
                print("\nFull content:")
                print("-" * 40)
                print(content)
                print("-" * 40)
            
            else:
                print("Invalid action.")
    
    def _edit_content(self, content):
        """
        Open content in an editor for modification
        
        Args:
            content: The content to edit
            
        Returns:
            Modified content
        """
        if not self.editor:
            return self._console_edit(content)
            
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as temp:
            temp_path = temp.name
            temp.write(content)
        
        try:
            # Open editor
            subprocess.call(f"{self.editor} {temp_path}", shell=True)
            
            # Read modified content
            with open(temp_path, "r") as f:
                modified_content = f.read()
                
            return modified_content
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _console_edit(self, content):
        """
        Simple console-based editor as fallback
        
        Args:
            content: The content to edit
            
        Returns:
            Modified content
        """
        print("\nConsole Editor:")
        print("Enter content line by line. Type ':wq' on a new line to save and exit.")
        print("Original content:")
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            print(f"{i+1}: {line}")
        
        new_lines = []
        print("\nEnter modified content:")
        
        line_num = 1
        while True:
            try:
                user_input = input(f"{line_num}: ")
                if user_input == ':wq':
                    break
                new_lines.append(user_input)
                line_num += 1
            except KeyboardInterrupt:
                print("\nEditing cancelled.")
                return content
            except EOFError:
                break
        
        if not new_lines:
            return content
        
        return "\n".join(new_lines)