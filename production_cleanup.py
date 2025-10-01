#!/usr/bin/env python3
"""
Final cleanup for operational site
Remove any remaining demo artifacts and prepare for client onboarding
"""

import re

def clean_for_production(text):
    """Clean up any remaining demo content for production"""
    
    # Replace any remaining demo language
    text = re.sub(r'demo|Demo|DEMO', 'analysis', text)
    text = re.sub(r'sample project|Sample Project', 'new project', text)
    text = re.sub(r'try it|Try It', 'analyze', text)
    text = re.sub(r'example|Example', 'template', text)
    
    # Clean up any test data placeholders
    text = re.sub(r'123 Oxford Street, London, W1D 2HX', '', text)
    
    return text

# Read the file
with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file size: {len(content)} characters")

# Clean for production
clean_content = clean_for_production(content)

print(f"After production cleanup: {len(clean_content)} characters")
print(f"Cleaned {len(content) - len(clean_content)} characters")

# Write back to file
with open('frontend/platform_clean.html', 'w', encoding='utf-8') as f:
    f.write(clean_content)

print("✅ Site prepared for client onboarding!")
print("✅ Professional neutral design with operational content")