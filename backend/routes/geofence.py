from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.geofence import Geofence
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, Polygon
import os
import requests
import json

geofence_bp = Blueprint('geofence', __name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check if API key is set before constructing URL
if GEMINI_API_KEY:
    # Using Gemini 2.0 Flash Experimental (v1beta API)
    GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}'
    print(f"[STARTUP] Geofence blueprint loaded. Gemini API Key: ✅ SET (length: {len(GEMINI_API_KEY)})")
    print(f"[STARTUP] Using model: gemini-2.0-flash-exp (v1beta API)")
else:
    GEMINI_API_URL = None
    print(f"[STARTUP] Geofence blueprint loaded. Gemini API Key: ❌ MISSING - Zone generation will not work!")

@geofence_bp.route('/list', methods=['GET'])
def list_geofences():
    active_only = request.args.get('active', 'true').lower() == 'true'
    query = Geofence.query
    if active_only:
        query = query.filter_by(active=True)
    geofences = query.all()
    return jsonify({'geofences': [gf.to_dict() for gf in geofences], 'count': len(geofences)}), 200

@geofence_bp.route('/check', methods=['POST'])
def check_geofence():
    data = request.get_json()
    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    point = Point(data['longitude'], data['latitude'])
    inside_geofences = []
    active_geofences = Geofence.query.filter_by(active=True).all()
    for geofence in active_geofences:
        try:
            polygon = to_shape(geofence.polygon)
            if polygon.contains(point):
                inside_geofences.append(geofence.to_dict())
        except:
            pass
    return jsonify({'inside_geofences': inside_geofences, 'count': len(inside_geofences)}), 200


@geofence_bp.route('/generate-nearby', methods=['POST'])
def generate_nearby_zones():
    """
    Dynamically generate safety zones for any location using Gemini AI
    This allows the system to work anywhere in the world!
    """
    try:
        # Check if Gemini API key is configured
        if not GEMINI_API_KEY or not GEMINI_API_URL:
            print("[Geofence] ❌ GEMINI_API_KEY not configured")
            return jsonify({
                'success': False,
                'error': 'AI service not configured. Please set GEMINI_API_KEY environment variable in Railway.',
                'zones': []
            }), 503  # Service Unavailable
        
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 10)  # Default 10km radius
        
        if not latitude or not longitude:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        print(f"[Geofence] Generating zones for location: {latitude}, {longitude}")
        
        # Create prompt for Gemini AI to generate safety zones
        prompt = f"""You are a safety advisor API. Based on GPS coordinates {latitude}, {longitude}, identify the city/area and provide 3-5 safety zones within {radius}km.

Return ONLY valid JSON with this EXACT structure:
[
  {{
    "name": "Area Name - Zone Type",
    "zone_type": "safe_zone/caution_zone/restricted",
    "risk_level": "low/medium/high",
    "description": "Brief safety description",
    "coordinates": [[lng1, lat1], [lng2, lat2], [lng3, lat3], [lng4, lat4]]
  }}
]

Guidelines:
- safe_zone: Tourist areas, malls, police stations, hotels (risk_level: low)
- caution_zone: Busy roads, markets, crowded areas (risk_level: medium)
- restricted: Government areas, isolated regions (risk_level: high)
- Coordinates should form a small rectangular area (0.01-0.02 degree difference)
- Base zones on real knowledge of the area

Return ONLY the JSON array, no markdown, no explanation."""

        # Call Gemini AI
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 2048,
            }
        }
        
        print(f"[Geofence] 🚀 Calling Gemini API...")
        print(f"[Geofence] Model: gemini-1.5-flash")
        
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
            print(f"[Geofence] ✅ Gemini API responded with status: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"[Geofence] ❌ Timeout after 30 seconds")
            return jsonify({
                'success': False,
                'error': 'AI service timeout',
                'zones': []
            }), 504
        except Exception as e:
            print(f"[Geofence] ❌ Connection error: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to connect: {str(e)}',
                'zones': []
            }), 500
        
        if response.status_code != 200:
            print(f"[Geofence] ❌ Gemini API Error:")
            print(f"[Geofence] Status: {response.status_code}")
            print(f"[Geofence] Body: {response.text[:500]}")
            
            # Handle rate limiting (429) - return empty zones
            if response.status_code == 429:
                print(f"[Geofence] ⚠️ Rate limit exceeded - returning existing zones")
                return jsonify({
                    'success': True,
                    'zones': [],
                    'message': 'Rate limit exceeded, showing existing zones only'
                }), 200
            
            return jsonify({
                'success': False,
                'error': f'AI service returned {response.status_code}',
                'details': response.text[:200],
                'zones': []
            }), 500
        
        result = response.json()
        
        if 'candidates' not in result or len(result['candidates']) == 0:
            print(f"[Geofence] No candidates in response: {result}")
            return jsonify({'error': 'No zones generated'}), 500
        
        candidate = result['candidates'][0]
        if 'content' not in candidate or 'parts' not in candidate['content']:
            print(f"[Geofence] Unexpected response structure: {result}")
            return jsonify({'error': 'Invalid AI response structure'}), 500
        
        text_response = candidate['content']['parts'][0]['text'].strip()
        
        # Clean markdown if present
        if text_response.startswith('```json'):
            text_response = text_response[7:]
        if text_response.startswith('```'):
            text_response = text_response[3:]
        if text_response.endswith('```'):
            text_response = text_response[:-3]
        text_response = text_response.strip()
        
        # Parse JSON
        zones_data = json.loads(text_response)
        
        # Save zones to database
        generated_zones = []
        for zone_data in zones_data:
            try:
                coords = zone_data['coordinates']
                # Close the polygon if not already closed
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                
                # Store polygon as GeoJSON text (model uses polygon_data field)
                polygon_geojson = {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
                
                # Create geofence
                geofence = Geofence(
                    name=zone_data['name'],
                    zone_type=zone_data['zone_type'],
                    risk_level=zone_data['risk_level'],
                    polygon_data=json.dumps(polygon_geojson),  # Store as JSON text
                    description=zone_data.get('description', 'Dynamically generated zone'),
                    active=True
                )
                db.session.add(geofence)
                generated_zones.append(zone_data['name'])
                print(f"[Geofence] Generated: {zone_data['name']}")
            except Exception as e:
                print(f"[Geofence] Error creating zone: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(generated_zones)} safety zones',
            'zones': generated_zones,
            'location': {'latitude': latitude, 'longitude': longitude}
        }), 200
        
    except json.JSONDecodeError as e:
        print(f"[Geofence] JSON Parse Error: {e}")
        return jsonify({'error': 'Failed to parse AI response'}), 500
    except Exception as e:
        print(f"[Geofence] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
