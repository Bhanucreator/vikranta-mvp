from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests
import json

cultural_bp = Blueprint('cultural', __name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check if API key is set before constructing URL
if GEMINI_API_KEY:
    # Using Gemini 2.0 Flash Experimental (v1beta API)
    GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}'
    print(f"[STARTUP] Cultural blueprint loaded. Gemini API Key: ✅ SET (length: {len(GEMINI_API_KEY)})")
    print(f"[STARTUP] Using model: gemini-2.0-flash-exp (v1beta API)")
else:
    GEMINI_API_URL = None
    print(f"[STARTUP] Cultural blueprint loaded. Gemini API Key: ❌ MISSING - Cultural features will not work!")

@cultural_bp.route('/nearby', methods=['POST'])
@jwt_required(optional=True)  # Make JWT optional for debugging
def get_nearby_cultural_places():
    """
    Get nearby cultural places based on current location using Gemini AI
    """
    print("\n" + "="*60)
    print("[CULTURAL] ✅ Route handler started!")
    print("="*60 + "\n")
    
    try:
        try:
            user_id = int(get_jwt_identity())  # Convert string back to int
            print(f"[Cultural] User {user_id} requesting nearby places")
        except:
            print("[Cultural] No JWT token, using anonymous access")
            user_id = "anonymous"
        
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 5)  # Default 5km radius
        language = data.get('language', 'en')  # Default English
        
        print(f"[Cultural] Location: {latitude}, {longitude}, Radius: {radius}km")
        
        if not latitude or not longitude:
            print("[Cultural] ERROR: Missing latitude or longitude")
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        if not GEMINI_API_KEY or not GEMINI_API_URL:
            print("[Cultural] ERROR: GEMINI_API_KEY not configured")
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured. Please set GEMINI_API_KEY environment variable in Railway.',
                'places': []
            }), 503  # Service Unavailable
        
        # Create prompt for Gemini AI
        prompt = f"""You are a tourist guide API. Return ONLY valid JSON, no markdown, no explanation.

Based on GPS coordinates {latitude}, {longitude}, return exactly 4 cultural/tourist places within {radius}km.

Return this EXACT JSON structure (ensure all strings are properly escaped):
[
  {{
    "name": "Place Name",
    "type": "temple/fort/palace/museum",
    "distance": 2.5,
    "rating": 4.5,
    "about": "Brief description in one line",
    "opening_hours": "9 AM - 5 PM",
    "entry_fee": "Rs 100 or Free",
    "best_time": "Morning",
    "dress_code": "Modest clothing",
    "photography": "Allowed",
    "etiquette": "Remove shoes",
    "safety_level": "safe",
    "safety_tips": "Watch belongings",
    "languages_spoken": "English, Local",
    "emergency_contact": "Police 100",
    "latitude": 12.9716,
    "longitude": 77.5946
  }}
]

IMPORTANT: Return ONLY the JSON array, no other text."""
        
        # Call Gemini AI API
        headers = {'Content-Type': 'application/json'}
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
                "maxOutputTokens": 4096,
            }
        }
        
        print(f"[Cultural] 🚀 Calling Gemini API...")
        print(f"[Cultural] API URL: {GEMINI_API_URL[:100]}...")
        
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
            print(f"[Cultural] ✅ Gemini API responded with status: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"[Cultural] ❌ Gemini API timeout after 30 seconds")
            return jsonify({
                'success': False,
                'error': 'Gemini API timeout - service is slow to respond',
                'places': []
            }), 504
        except Exception as e:
            print(f"[Cultural] ❌ Gemini API connection error: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to connect to Gemini API: {str(e)}',
                'places': []
            }), 500
        
        if response.status_code != 200:
            print(f"[Cultural] ❌ Gemini API Error Response:")
            print(f"[Cultural] Status: {response.status_code}")
            print(f"[Cultural] Body: {response.text[:500]}")  # First 500 chars
            
            # Handle rate limiting (429) - return empty array instead of error
            if response.status_code == 429:
                print(f"[Cultural] ⚠️ Rate limit exceeded - returning empty results")
                return jsonify({
                    'success': True,  # Don't treat as error
                    'places': [],
                    'message': 'Rate limit exceeded, please wait a moment and try again'
                }), 200  # Return 200 to avoid frontend error
            
            return jsonify({
                'success': False,
                'error': f'Gemini API returned {response.status_code}',
                'details': response.text[:200],
                'places': []
            }), 500
        
        result = response.json()
        print(f"[Cultural] 📦 Response keys: {list(result.keys())}")
        
        # Extract text from Gemini response
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            
            # Check if content exists
            if 'content' not in candidate or 'parts' not in candidate['content']:
                print(f"[Cultural] ❌ No content in response: {result}")
                return jsonify({'error': 'No content from Gemini AI'}), 500
            
            text_response = candidate['content']['parts'][0]['text']
            print(f"[Cultural] 📝 Raw response length: {len(text_response)} chars")
            
            # Clean up the response (remove markdown code blocks if present)
            text_response = text_response.strip()
            if text_response.startswith('```json'):
                text_response = text_response[7:]
            if text_response.startswith('```'):
                text_response = text_response[3:]
            if text_response.endswith('```'):
                text_response = text_response[:-3]
            text_response = text_response.strip()
            
            # Try to parse JSON
            try:
                places_data = json.loads(text_response)
                print(f"[Cultural] ✅ Successfully parsed {len(places_data)} places")
            except json.JSONDecodeError as e:
                print(f"[Cultural] ❌ JSON Parse Error: {e}")
                print(f"[Cultural] 📄 Response text (first 500 chars): {text_response[:500]}")
                return jsonify({'error': 'Failed to parse AI response - invalid JSON'}), 500
            
            return jsonify({
                'success': True,
                'places': places_data,
                'user_location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            }), 200
        else:
            print(f"[Cultural] ❌ No candidates in response")
            return jsonify({'error': 'No response from Gemini AI'}), 500
            
    except json.JSONDecodeError as e:
        print(f"[Cultural] ❌ Outer JSON Parse Error: {e}")
        return jsonify({'error': 'Failed to parse AI response'}), 500
    except Exception as e:
        print(f"[Cultural] ❌ Error fetching cultural places: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@cultural_bp.route('/events', methods=['GET'])
def get_cultural_events():
    """
    Get current cultural events/festivals happening at the user's location
    Uses Gemini AI to fetch real-time local events
    """
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        
        if not latitude or not longitude:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        print(f"[Cultural Events] Fetching events for: {latitude}, {longitude}")
        
        if not GEMINI_API_KEY:
            print("[Cultural Events] ERROR: GEMINI_API_KEY not configured")
            # Return fallback event
            return jsonify({
                'success': True,
                'event': {
                    'name': 'Local Festival',
                    'date': 'Check local calendar'
                }
            }), 200
        
        # Create prompt for Gemini AI to get current events
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are a local events API. Return ONLY valid JSON, no markdown.

Based on GPS coordinates {latitude}, {longitude} and today's date {current_date}, 
what is ONE major cultural event, festival, or celebration happening RIGHT NOW or in the next 7 days in this area?

Return this EXACT JSON structure:
{{
  "name": "Event Name",
  "date": "Date or date range",
  "location": "City/Area Name",
  "description": "One sentence about the event",
  "type": "festival/celebration/cultural event"
}}

If no major event, return a typical local cultural practice or upcoming holiday.
Return ONLY the JSON object, no other text."""
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 1024,
            }
        }
        
        print(f"[Cultural Events] 🚀 Calling Gemini API...")
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"[Cultural Events] ❌ Gemini API Error: {response.text}")
            # Return fallback
            return jsonify({
                'success': True,
                'event': {
                    'name': 'Local Festival',
                    'date': 'Check local calendar'
                }
            }), 200
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            
            if 'content' in candidate and 'parts' in candidate['content']:
                text_response = candidate['content']['parts'][0]['text'].strip()
                
                # Clean markdown
                if text_response.startswith('```json'):
                    text_response = text_response[7:]
                if text_response.startswith('```'):
                    text_response = text_response[3:]
                if text_response.endswith('```'):
                    text_response = text_response[:-3]
                text_response = text_response.strip()
                
                try:
                    event_data = json.loads(text_response)
                    print(f"[Cultural Events] ✅ Found event: {event_data.get('name', 'Unknown')}")
                    
                    return jsonify({
                        'success': True,
                        'event': event_data
                    }), 200
                except json.JSONDecodeError as e:
                    print(f"[Cultural Events] ❌ JSON Parse Error: {e}")
        
        # Fallback if parsing fails
        return jsonify({
            'success': True,
            'event': {
                'name': 'Local Cultural Activities',
                'date': 'Ongoing'
            }
        }), 200
        
    except Exception as e:
        print(f"[Cultural Events] Error: {str(e)}")
        return jsonify({
            'success': True,
            'event': {
                'name': 'Local Festival',
                'date': 'Check local calendar'
            }
        }), 200


@cultural_bp.route('/place/<place_id>', methods=['GET'])
@jwt_required()
def get_place_details(place_id):
    """
    Get detailed information about a specific cultural place
    """
    try:
        # This can be enhanced later to fetch from database
        # For now, this endpoint is for future expansion
        return jsonify({
            'success': True,
            'message': 'Place details endpoint - to be implemented'
        }), 200
        
    except Exception as e:
        print(f"Error fetching place details: {str(e)}")
        return jsonify({'error': str(e)}), 500


@cultural_bp.route('/directions', methods=['POST'])
@jwt_required()
def get_directions():
    """
    Get directions from current location to a cultural place
    """
    try:
        data = request.get_json()
        from_lat = data.get('from_latitude')
        from_lng = data.get('from_longitude')
        to_lat = data.get('to_latitude')
        to_lng = data.get('to_longitude')
        
        if not all([from_lat, from_lng, to_lat, to_lng]):
            return jsonify({'error': 'All coordinates are required'}), 400
        
        # Use Mapbox Directions API (can be implemented)
        # For now, return basic direction info
        
        return jsonify({
            'success': True,
            'directions_url': f'https://www.google.com/maps/dir/?api=1&origin={from_lat},{from_lng}&destination={to_lat},{to_lng}&travelmode=driving'
        }), 200
        
    except Exception as e:
        print(f"Error getting directions: {str(e)}")
        return jsonify({'error': str(e)}), 500
