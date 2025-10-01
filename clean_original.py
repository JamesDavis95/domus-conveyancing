#!/usr/bin/env python3
"""
Clean the original dark theme design - ONLY remove emojis and demo content
Keep all design, colors, and styling exactly the same
"""

import re

def clean_original_design(text):
    """Remove only emojis and obvious demo content, preserve everything else"""
    
    # 1. Remove emojis only
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs  
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F700-\U0001F77F"  # alchemical
        "\U0001F780-\U0001F7FF"  # geometric shapes
        "\U0001F800-\U0001F8FF"  # supplemental arrows
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\uFE00-\uFE0F"          # variation selectors
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # 2. Clean up any obvious demo text (be very careful here)
    # Only remove very obvious demo markers
    text = re.sub(r'\[DEMO\]|\[Sample\]|\[Example\]', '', text, flags=re.IGNORECASE)
    
    return text

# Read the original design
with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original design file size: {len(content)} characters")

# Clean only emojis and demo content
cleaned_content = clean_original_design(content)

print(f"After cleaning: {len(cleaned_content)} characters")
print(f"Removed {len(content) - len(cleaned_content)} characters")

# Write back
with open('frontend/platform_clean.html', 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

print("✅ Original dark theme design cleaned - emojis and demo content removed!")
print("✅ All colors, styling, and design preserved exactly as original")