from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests
import json
from datetime import datetime, timedelta
from utils.fallback_data import get_fallback_cultural_places

cultural_bp = Blueprint('cultural', __name__)

# Cache for Gemini API responses (in-memory cache)
_cultural_cache = {}
_events_cache = {}
CACHE_DURATION_MINUTES = 60

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check if API key is set before constructing URL
if GEMINI_API_KEY:
    # Using Gemini 2.0 Flash (stable version)
    GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}'
    print(f"[STARTUP] Cultural blueprint loaded. Gemini API Key: ✅ SET (length: {len(GEMINI_API_KEY)})")
    print(f"[STARTUP] Using model: gemini-2.0-flash (v1beta API)")
else:
    GEMINI_API_URL = None
    print(f"[STARTUP] Cultural blueprint loaded. Gemini API Key: ❌ MISSING - Cultural features will not work!")

@cultural_bp.route('/events', methods=['GET'])
@jwt_required(optional=True)
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
        
        data = request.args
        latitude = data.get('latitude', type=float)
        longitude = data.get('longitude', type=float)
        radius = data.get('radius', 5, type=int)  # Default 5km radius
        language = data.get('language', 'en')  # Default English
        
        print(f"[Cultural] Location: {latitude}, {longitude}, Radius: {radius}km")
        
        if not latitude or not longitude:
            print("[Cultural] ERROR: Missing latitude or longitude")
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Create cache key based on location (rounded to 2 decimal places)
        cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}_{radius}_{language}"
        
        # Check cache first
        if cache_key in _cultural_cache:
            cached_data, cached_time = _cultural_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                print(f"[Cultural] ✅ Returning cached places for {cache_key} (age: {(datetime.now() - cached_time).seconds}s)")
                return jsonify({
                    'success': True,
                    'places': cached_data,
                    'user_location': {'latitude': latitude, 'longitude': longitude},
                    'cached': True
                }), 200
            else:
                # Cache expired
                print(f"[Cultural] 🕐 Cache expired for {cache_key}")
                del _cultural_cache[cache_key]
        
        if not GEMINI_API_KEY or not GEMINI_API_URL:
            print("[Cultural] ⚠️ WARNING: GEMINI_API_KEY not configured. Using fallback data.")
            return jsonify({
                'success': True,
                'places': get_fallback_cultural_places(),
                'message': 'Displaying sample data. API key not configured.'
            }), 200
        
        # Create a more concise prompt for Gemini AI to reduce token usage
        prompt = f"""As a guide API, return a JSON array of 4 cultural places near {latitude},{longitude} within {radius}km.
JSON structure must be:
[
  {{
    "name": "Place Name", "type": "historic|museum|etc", "distance": 2.5, "rating": 4.5, "about": "Brief description",
    "opening_hours": "10 AM - 5 PM", "entry_fee": "₹100", "best_time": "Morning", "dress_code": "Casual",
    "photography": "Allowed", "etiquette": "Be respectful", "safety_level": "safe", "safety_tips": "Stay alert",
    "languages_spoken": "English, Local", "emergency_contact": "100", "latitude": 12.9716, "longitude": 77.5946
  }}
]
Return ONLY the JSON array. No other text or markdown.
"""
        
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
            print(f"[Cultural] ❌ Gemini API timeout after 30 seconds. Using fallback data.")
            return jsonify({
                'success': True,
                'places': get_fallback_cultural_places(),
                'message': 'API timeout. Displaying sample data.'
            }), 200
        except Exception as e:
            print(f"[Cultural] ❌ Gemini API connection error: {e}. Using fallback data.")
            return jsonify({
                'success': True,
                'places': get_fallback_cultural_places(),
                'message': f'API connection error. Displaying sample data.'
            }), 200
        
        if response.status_code != 200:
            error_body = response.text
            print(f"[Cultural] ❌ Gemini API Error Response:")
            print(f"[Cultural] Status: {response.status_code}")
            print(f"[Cultural] Full Body: {error_body}")  # Log the full body
            
            # Handle rate limiting (429) - return fallback data
            if response.status_code == 429:
                print(f"[Cultural] ⚠️ Rate limit exceeded - returning fallback data")
                return jsonify({
                    'success': True,
                    'places': get_fallback_cultural_places(),
                    'message': 'Rate limit exceeded. Displaying sample data.'
                }), 200
            
            # Return a 500 error so the frontend knows something went wrong
            return jsonify({
                'success': False,
                'message': f'Failed to retrieve data from Gemini API. Status: {response.status_code}',
                'error_details': error_body 
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
                
                # Cache the successful response
                _cultural_cache[cache_key] = (places_data, datetime.now())
                print(f"[Cultural] ✅ Cached places for {cache_key}")
            except json.JSONDecodeError as e:
                print(f"[Cultural] ❌ JSON Parse Error: {e}. Using fallback data.")
                print(f"[Cultural] 📄 Response text (first 500 chars): {text_response[:500]}")
                return jsonify({
                    'success': True,
                    'places': get_fallback_cultural_places(),
                    'message': 'Failed to parse AI response. Displaying sample data.'
                }), 200
            
            return jsonify({
                'success': True,
                'places': places_data,
                'user_location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            }), 200
        else:
            print(f"[Cultural] ❌ No candidates in response. Using fallback data.")
            return jsonify({
                'success': True,
                'places': get_fallback_cultural_places(),
                'message': 'No response from AI. Displaying sample data.'
            }), 200
            
    except json.JSONDecodeError as e:
        print(f"[Cultural] ❌ Outer JSON Parse Error: {e}. Using fallback data.")
        return jsonify({
            'success': True,
            'places': get_fallback_cultural_places(),
            'message': 'Failed to parse AI response. Displaying sample data.'
        }), 200
    except Exception as e:
        print(f"[Cultural] ❌ Error fetching cultural places: {str(e)}. Using fallback data.")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': True,
            'places': get_fallback_cultural_places(),
            'message': f'An error occurred: {str(e)}. Displaying sample data.'
        }), 200


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
        
        # Create cache key
        cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}_events"
        
        # Check cache first
        if cache_key in _events_cache:
            cached_data, cached_time = _events_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                print(f"[Cultural Events] ✅ Returning cached event for {cache_key}")
                return jsonify({
                    'success': True,
                    'event': cached_data,
                    'cached': True
                }), 200
            else:
                del _events_cache[cache_key]
        
        if not GEMINI_API_KEY:
            print("[Cultural Events] ⚠️ WARNING: GEMINI_API_KEY not configured. Using fallback event.")
            # Return fallback event
            return jsonify({
                'success': True,
                'event': {
                    'name': 'Local Festival',
                    'date': 'Check local calendar'
                }
            }), 200
        
        # Create prompt for Gemini AI to get current events
        from datetime import datetime as dt
        current_date = dt.now().strftime("%B %d, %Y")
        
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
            print(f"[Cultural Events] ❌ Gemini API Error: {response.text}. Using fallback event.")
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
                    
                    # Cache the successful response
                    _events_cache[cache_key] = (event_data, datetime.now())
                    print(f"[Cultural Events] ✅ Cached event for {cache_key}")
                    
                    return jsonify({
                        'success': True,
                        'event': event_data
                    }), 200
                except json.JSONDecodeError as e:
                    print(f"[Cultural Events] ❌ JSON Parse Error: {e}. Using fallback event.")
        
        # Fallback if parsing fails or no candidates
        print("[Cultural Events] ⚠️ Using fallback event data.")
        return jsonify({
            'success': True,
            'event': {
                'name': 'Local Cultural Activities',
                'date': 'Ongoing'
            }
        }), 200
        
    except Exception as e:
        print(f"[Cultural Events] ❌ Error: {str(e)}. Using fallback event.")
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
