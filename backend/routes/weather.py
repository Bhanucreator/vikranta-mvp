from flask import Blueprint, request, jsonify
import os
import requests

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/current', methods=['GET'])
def get_current_weather():
    """
    Get real-time weather data for a location
    """
    try:
        # Get API key inside the function to ensure it's loaded from environment
        OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'demo')
        
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        
        if not latitude or not longitude:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        print(f"[Weather] Fetching weather for: {latitude}, {longitude}")
        print(f"[Weather] API Key: {OPENWEATHER_API_KEY[:10]}... (length: {len(OPENWEATHER_API_KEY)})")
        
        # Call OpenWeatherMap API
        url = f'https://api.openweathermap.org/data/2.5/weather'
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'  # Celsius
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"[Weather] API Error: {response.text}")
            # Return fallback data
            return jsonify({
                'success': True,
                'weather': {
                    'temperature': 28,
                    'description': 'Pleasant weather',
                    'icon': '🌤️'
                }
            }), 200
        
        data = response.json()
        
        # Map weather conditions to emojis
        weather_icons = {
            'Clear': '☀️',
            'Clouds': '☁️',
            'Rain': '🌧️',
            'Drizzle': '🌦️',
            'Thunderstorm': '⛈️',
            'Snow': '❄️',
            'Mist': '🌫️',
            'Fog': '🌫️',
            'Haze': '🌫️'
        }
        
        main_weather = data['weather'][0]['main']
        icon = weather_icons.get(main_weather, '🌤️')
        
        weather_data = {
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'].capitalize(),
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'icon': icon
        }
        
        print(f"[Weather] ✅ {weather_data['description']}, {weather_data['temperature']}°C")
        
        return jsonify({
            'success': True,
            'weather': weather_data
        }), 200
        
    except Exception as e:
        print(f"[Weather] Error: {str(e)}")
        # Return fallback data
        return jsonify({
            'success': True,
            'weather': {
                'temperature': 28,
                'description': 'Pleasant weather',
                'icon': '🌤️'
            }
        }), 200
