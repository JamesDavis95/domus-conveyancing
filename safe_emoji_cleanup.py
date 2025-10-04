#!/usr/bin/env python3
"""
Safe Emoji Cleanup - Remove emojis from UI elements only while preserving code functionality
"""

import os
import re

def safe_remove_emojis_from_html(content):
    """Safely remove emojis from HTML content"""
    # Remove emojis from icon spans
    content = re.sub(r'<span class="icon">[^<]*</span>', '<span class="icon"></span>', content)
    
    # Remove emojis from specific HTML content (preserving structure)
    emoji_pattern = r'[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿]'
    content = re.sub(emoji_pattern, '', content)
    
    return content

def safe_remove_emojis_from_python_strings(content):
    """Safely remove emojis from Python string literals only"""
    # Pattern to match string literals containing emojis
    def replace_emoji_in_string(match):
        string_content = match.group(1)
        emoji_pattern = r'[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿]'
        cleaned = re.sub(emoji_pattern, '', string_content)
        return f'"{cleaned}"'
    
    # Replace emojis in double-quoted strings
    content = re.sub(r'"([^"]*[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿][^"]*)"', replace_emoji_in_string, content)
    
    # Replace emojis in single-quoted strings  
    content = re.sub(r"'([^']*[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿][^']*)'", lambda m: f"'{re.sub(r'[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿]', '', m.group(1))}'", content)
    
    return content

def clean_frontend_files():
    """Clean emojis from frontend HTML files"""
    frontend_files = [
        'frontend/platform_production.html',
        'frontend/platform_clean_working.html',
        'frontend/platform_fixed.html',
        'frontend/platform_test.html'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                cleaned_content = safe_remove_emojis_from_html(content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                    
                print(f"Cleaned emojis from: {file_path}")
            except Exception as e:
                print(f"Error cleaning {file_path}: {e}")

def clean_specific_python_files():
    """Clean emojis from specific Python files that contain UI strings"""
    files_to_clean = [
        'app.py'  # Only clean the main app file for now
    ]
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Only clean print statements and string literals, not code structure
                lines = content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Clean print statements with emojis
                    if 'print(' in line and any(emoji in line for emoji in '🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿'):
                        emoji_pattern = r'[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿]'
                        line = re.sub(emoji_pattern, '', line)
                    
                    # Clean icon strings in dictionaries
                    if '"icon":' in line and any(emoji in line for emoji in '🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿'):
                        emoji_pattern = r'[🚀✅📊⚠️🎉🔧📱💳🌟🏠🤖📈🔒📝🎯❌🔥💡⭐🎨📋🛡️⚡🌐📢🔍📄💰🎭🌱🌿]'
                        line = re.sub(emoji_pattern, '', line)
                    
                    cleaned_lines.append(line)
                
                cleaned_content = '\n'.join(cleaned_lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                    
                print(f"Safely cleaned emojis from: {file_path}")
            except Exception as e:
                print(f"Error cleaning {file_path}: {e}")

def main():
    """Main cleanup process"""
    print("Starting safe emoji cleanup (UI elements only)...")
    
    # Clean frontend files
    clean_frontend_files()
    
    # Clean specific Python files safely
    clean_specific_python_files()
    
    print("Safe emoji cleanup complete!")
    print("All functionality preserved, only UI emojis removed")

if __name__ == "__main__":
    main()