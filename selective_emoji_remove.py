#!/usr/bin/env python3
"""
Selective emoji removal from platform_clean.html
Removes only emoji characters while preserving all design and structure
"""

import re

def remove_emojis_only(text):
    """Remove only emoji characters, preserve all other content"""
    # More targeted emoji pattern - only actual emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs  
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\uFE00-\uFE0F"          # variation selectors
        "\U0001F000-\U0001F02F"  # mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # playing cards
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

# Read the file
with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file size: {len(content)} characters")

# Remove only emojis
clean_content = remove_emojis_only(content)

print(f"After selective emoji removal: {len(clean_content)} characters")
print(f"Removed {len(content) - len(clean_content)} characters")

# Write back to file
with open('frontend/platform_clean.html', 'w', encoding='utf-8') as f:
    f.write(clean_content)

print("✅ Selective emoji removal complete - design preserved!")