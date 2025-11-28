#!/usr/bin/env python3
"""
Test script to verify Gemini API is working
Uses your $100K Google Cloud credits!
"""

import google.generativeai as genai

# Configure Gemini with your API key
GEMINI_API_KEY = "AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize model (using latest Gemini 2.5 Pro - the best!)
model = genai.GenerativeModel('gemini-2.5-pro')

print("🤖 Testing Google Gemini AI...")
print("=" * 50)
print()

# Test 1: Simple question
print("Test 1: Simple Question")
print("Q: Who is Cole Caufield?")
response = model.generate_content("Who is Cole Caufield? Give me a brief 2-sentence answer about the NHL player.")
print(f"A: {response.text}")
print()

# Test 2: SQL generation
print("Test 2: SQL Query Generation")
print("Q: Generate SQL for top 5 scorers")
sql_prompt = """Generate a PostgreSQL query to find the top 5 NHL scorers.
Schema: player_career_stats (player_id, season, goals, assists, points)
        players (id, full_name, position_code)
Use season='20242025'. Return ONLY the SQL query."""

response = model.generate_content(sql_prompt)
print(f"Generated SQL:\n{response.text}")
print()

# Test 3: Fantasy advice
print("Test 3: Fantasy Hockey Advice")
print("Q: Should I trade for Nathan MacKinnon?")
response = model.generate_content("Should I trade for Nathan MacKinnon in fantasy hockey? Give me a 3-sentence analysis.")
print(f"A: {response.text}")
print()

print("=" * 50)
print("✅ All tests passed!")
print("💰 Using your $100K Google Cloud credits")
print("🚀 Ready to integrate into your app!")

