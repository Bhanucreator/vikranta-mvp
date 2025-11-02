from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User, UserLocation
from models.geofence import Geofence
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from datetime import datetime, timedelta

location_bp = Blueprint('location', __name__)

@location_bp.route('/update', methods=['POST'])
@jwt_required(optional=True)
def update_location():
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)  # Convert string back to int
            print(f"[Location] User {user_id} updating location")
        else:
            print("[Location] No JWT token, using anonymous")
            user_id = 1  # Use a default user for testing
    except:
        print("[Location] JWT error, using default user")
        user_id = 1
    data = request.get_json()
    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    location = UserLocation(
        user_id=user_id,
        latitude=data['latitude'],
        longitude=data['longitude'],
        accuracy=data.get('accuracy')
    )
    db.session.add(location)
    db.session.commit()
    point = Point(data['longitude'], data['latitude'])
    geofence_alerts = []
    active_geofences = Geofence.query.filter_by(active=True).all()
    for geofence in active_geofences:
        try:
            polygon = to_shape(geofence.polygon)
            if polygon.contains(point):
                geofence_alerts.append({
                    'id': geofence.id,
                    'name': geofence.name,
                    'zone_type': geofence.zone_type,
                    'risk_level': geofence.risk_level,
                    'warning_message': geofence.warning_message or f'You are entering {geofence.name}',
                    'description': geofence.description
                })
        except:
            pass
    return jsonify({'message': 'Location updated successfully', 'location_id': location.id, 'geofence_alerts': geofence_alerts}), 200

@location_bp.route('/history', methods=['GET'])
@jwt_required()
def get_location_history():
    user_id = int(get_jwt_identity())  # Convert string back to int
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    locations = UserLocation.query.filter(
        UserLocation.user_id == user_id,
        UserLocation.timestamp >= since
    ).order_by(UserLocation.timestamp.desc()).all()
    return jsonify({'locations': [loc.to_dict() for loc in locations], 'count': len(locations)}), 200

@location_bp.route('/all-tourists', methods=['GET'])
@jwt_required()
def get_all_tourist_locations():
    """Get real-time locations of all active tourists (authorities only)"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Only authorities can see all tourist locations
    if user.role != 'authority':
        return jsonify({'error': 'Unauthorized - Authority access required'}), 403
    
    # Get latest location for each tourist
    # Get all tourists
    tourists = User.query.filter_by(role='tourist').all()
    
    tourist_locations = []
    for tourist in tourists:
        # Get most recent location
        latest_location = UserLocation.query.filter_by(user_id=tourist.id).order_by(UserLocation.timestamp.desc()).first()
        
        if latest_location:
            tourist_locations.append({
                'user_id': tourist.id,
                'user_name': tourist.name,
                'user_email': tourist.email,
                'user_phone': tourist.phone,
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'accuracy': latest_location.accuracy,
                'timestamp': latest_location.timestamp.isoformat(),
                'last_seen': get_time_ago(latest_location.timestamp)
            })
    
    return jsonify({
        'locations': tourist_locations,
        'count': len(tourist_locations),
        'timestamp': datetime.now().isoformat()
    }), 200

def get_time_ago(timestamp):
    """Get human-readable time difference"""
    now = datetime.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds/60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h ago"
    else:
        return f"{int(seconds/86400)}d ago"
