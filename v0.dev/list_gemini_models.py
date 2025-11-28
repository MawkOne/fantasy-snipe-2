#!/usr/bin/env python3
"""List available Gemini models"""

import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk"
genai.configure(api_key=GEMINI_API_KEY)

print("🔍 Listing available Gemini models...")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Description: {model.description}")
        print(f"   Methods: {', '.join(model.supported_generation_methods)}")
        print()

print("=" * 60)

