#!/usr/bin/env python3
"""
Test script to verify Gemini API key works
Run this locally to test before deploying
"""

import os
import requests
import json

# Set your API key
GEMINI_API_KEY = "AIzaSyA5y7UBk7Nj3DJeFEy8ojLqJIcrZuptJY4"  # Replace with your actual key

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set!")
    exit(1)

print(f"✅ API Key length: {len(GEMINI_API_KEY)}")
print(f"✅ API Key starts with: {GEMINI_API_KEY[:10]}...")

# Test URL construction  
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}'
print(f"\n🔗 API URL: {GEMINI_API_URL[:100]}...")

# Test API call
prompt = "Return only the JSON: [{\"name\": \"Test Place\", \"type\": \"temple\"}]"

payload = {
    "contents": [{
        "parts": [{
            "text": prompt
        }]
    }],
    "generationConfig": {
        "temperature": 0.4,
        "topK": 32,
        "topP": 1,
        "maxOutputTokens": 1024,
    }
}

print("\n🚀 Testing Gemini API...")
try:
    response = requests.post(GEMINI_API_URL, 
                            headers={'Content-Type': 'application/json'},
                            json=payload,
                            timeout=10)
    
    print(f"\n📡 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Gemini API is working!")
        result = response.json()
        print(f"📦 Response keys: {list(result.keys())}")
        
        if 'candidates' in result:
            print(f"✅ Got {len(result['candidates'])} candidate(s)")
            if len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"📝 Response text: {text[:200]}...")
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        # Common errors
        if response.status_code == 400:
            print("\n⚠️ Error 400: Bad Request - Check if:")
            print("   1. API key is valid")
            print("   2. Model name is correct (gemini-pro for v1 API)")
            print("   3. Payload format is correct")
        elif response.status_code == 403:
            print("\n⚠️ Error 403: Forbidden - API key might be:")
            print("   1. Invalid or expired")
            print("   2. Not enabled for this API")
            print("   3. Restricted by IP or domain")
        elif response.status_code == 429:
            print("\n⚠️ Error 429: Rate limit exceeded")
            print("   Wait a few minutes and try again")
            
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("If you see '✅ SUCCESS' above, your API key works!")
print("Copy this key to Railway environment variable: GEMINI_API_KEY")
print("="*60)
