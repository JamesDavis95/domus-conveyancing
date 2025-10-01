#!/usr/bin/env python3
"""
Complete emoji removal for the neutral design
Remove all emojis while preserving the dark theme design
"""

import re

def remove_all_emojis(text):
    """Comprehensive emoji removal"""
    # Extended emoji pattern to catch everything
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
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F000-\U0001F02F"  # mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # playing cards
        "\U00002300-\U000023FF"  # miscellaneous technical
        "\U0001F100-\U0001F1FF"  # enclosed alphanumeric supplement
        "\U0001F200-\U0001F2FF"  # enclosed cjk letters and months
        "\U0001F400-\U0001F4FF"  # miscellaneous symbols and pictographs
        "\U0001F500-\U0001F5FF"  # miscellaneous symbols and arrows
        "\U0001F600-\U0001F6FF"  # emoticons and transport
        "\U0001F700-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FAFF"  # extended pictographs
        "\uFE00-\uFE0F"          # variation selectors
        "\u2640-\u2642"          # gender symbols
        "\u2600-\u2B55"          # miscellaneous symbols and arrows
        "\u200d"                 # zero width joiner
        "\u23cf"                 # eject symbol
        "\u23e9-\u23f3"          # media symbols
        "\u231a-\u231b"          # watch symbols
        "\u3030"                 # wavy dash
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

# Read the file
with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file size: {len(content)} characters")

# Remove all emojis
clean_content = remove_all_emojis(content)

print(f"After emoji removal: {len(clean_content)} characters")
print(f"Removed {len(content) - len(clean_content)} characters")

# Write back to file
with open('frontend/platform_clean.html', 'w', encoding='utf-8') as f:
    f.write(clean_content)

print("✅ All emojis removed from neutral design!")
print("✅ Dark theme with neutral colors preserved")