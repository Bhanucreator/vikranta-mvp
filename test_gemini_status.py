import requests
import time
import json

API_URL = "https://vikranta-mvp-production.up.railway.app/api/cultural/nearby"

print("🔍 Monitoring Gemini API rate limit status...")
print("=" * 60)

attempt = 1
while attempt <= 10:
    print(f"\n⏳ Attempt {attempt}/10...")
    
    try:
        response = requests.post(API_URL, json={
            "latitude": 12.9564672,
            "longitude": 77.594624,
            "radius": 5
        }, timeout=10)
        
        data = response.json()
        
        if data.get('success') and data.get('places') and len(data['places']) > 0:
            print("✅ SUCCESS! Gemini API is working!")
            print(f"📍 Got {len(data['places'])} cultural places:")
            for place in data['places']:
                print(f"   - {place.get('name', 'Unknown')}")
            break
        elif 'rate limit' in data.get('message', '').lower():
            print(f"⚠️  Still rate limited. Waiting 30 seconds...")
        else:
            print(f"⚠️  Empty response. Waiting 30 seconds...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if attempt < 10:
        time.sleep(30)  # Wait 30 seconds between attempts
    attempt += 1

print("\n" + "=" * 60)
print("Test complete!")
