#!/usr/bin/env python3
"""Remove all emojis from platform_clean.html"""

import re

def remove_emojis(text):
    """Remove all emoji characters from text"""
    # Unicode ranges for emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

# Read the file
with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file size: {len(content)} characters")

# Remove emojis
clean_content = remove_emojis(content)

print(f"After emoji removal: {len(clean_content)} characters")
print(f"Removed {len(content) - len(clean_content)} characters")

# Write back to file
with open('frontend/platform_clean.html', 'w', encoding='utf-8') as f:
    f.write(clean_content)

print("✅ Emojis removed successfully!")