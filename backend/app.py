from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import config
from extensions import db, jwt, mail
from datetime import datetime
import os

# Global SocketIO instance - will be initialized in create_app
socketio = None

def create_app(config_name=None):
    """Application factory pattern"""
    global socketio
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Configure CORS with explicit settings
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }})
    
    # Initialize SocketIO for real-time communication
    # IMPORTANT: Assign to global variable so it can be imported by routes
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        logger=True,  # Enable logging for debugging
        engineio_logger=False,  # Disable verbose engine.io logs
        ping_timeout=60,  # Increase timeout for slower connections
        ping_interval=25,  # Send pings every 25 seconds
        max_http_buffer_size=1e8,  # Increase buffer size for large messages
        allow_upgrades=True,  # Allow transport upgrades (polling -> websocket)
        transports=['polling', 'websocket']  # Support both transports
    )
    
    print(f"✅ SocketIO initialized: {socketio is not None}")
    print(f"✅ SocketIO type: {type(socketio)}")
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.location import location_bp
    from routes.incident import incident_bp
    from routes.geofence import geofence_bp
    from routes.cultural import cultural_bp
    from routes.weather import weather_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(location_bp, url_prefix='/api/location')
    app.register_blueprint(incident_bp, url_prefix='/api/incident')
    app.register_blueprint(geofence_bp, url_prefix='/api/geofence')
    app.register_blueprint(cultural_bp, url_prefix='/api/cultural')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    
    # WebSocket event handlers
    @socketio.on('connect')
    def handle_connect():
        print(f"🔌 Client connected: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"🔌 Client disconnected: {request.sid}")
    
    @socketio.on('join_authority_room')
    def handle_join_authority():
        """Authority joins room to receive real-time alerts"""
        join_room('authorities')
        print(f"👮 Authority joined alert room: {request.sid}")
        emit('joined', {'room': 'authorities'})
    
    @socketio.on('join_incident_room')
    def handle_join_incident(data):
        """Join specific incident chat room"""
        incident_id = data.get('incident_id')
        if incident_id:
            room = f"incident_{incident_id}"
            join_room(room)
            print(f"💬 User joined incident room: {room}")
            emit('joined_chat', {'incident_id': incident_id})
    
    @socketio.on('join_user_room')
    def handle_join_user_room(data):
        """Tourist joins their personal room to receive incident status notifications"""
        user_id = data.get('user_id')
        if user_id:
            room = f"user_{user_id}"
            join_room(room)
            print(f"👤 Tourist {user_id} joined personal notification room: {room}")
            emit('joined_user_room', {'user_id': user_id, 'room': room})
    
    @socketio.on('send_message')
    def handle_message(data):
        """Handle chat messages in incident rooms"""
        incident_id = data.get('incident_id')
        message = data.get('message')
        sender_name = data.get('sender_name')
        sender_role = data.get('sender_role')
        
        if incident_id and message:
            room = f"incident_{incident_id}"
            emit('new_message', {
                'incident_id': incident_id,
                'message': message,
                'sender_name': sender_name,
                'sender_role': sender_role,
                'timestamp': datetime.now().isoformat()
            }, room=room)
            print(f"💬 Message sent to {room}: {message[:50]}...")
    
    # Request logging
    @app.before_request
    def log_request():
        from flask import request
        print(f"\n{'='*60}")
        print(f"[REQUEST] {request.method} {request.path}")
        print(f"[HEADERS] Authorization: {request.headers.get('Authorization', 'NONE')[:50]}...")
        print(f"[CONTENT-TYPE] {request.headers.get('Content-Type', 'NONE')}")
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                print(f"[BODY] {request.get_json()}")
            except:
                print(f"[BODY] Could not parse JSON")
        print(f"{'='*60}\n")
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"[JWT] Token expired for user: {jwt_payload.get('sub')}")
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please log in again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"[JWT] Invalid token: {error}")
        return jsonify({
            'error': 'Invalid token',
            'message': 'Signature verification failed'
        }), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"[JWT] Missing token: {error}")
        return jsonify({
            'error': 'Authorization required',
            'message': 'Request does not contain an access token'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        print(f"[JWT] Revoked token for user: {jwt_payload.get('sub')}")
        return jsonify({
            'error': 'Token has been revoked',
            'message': 'Please log in again'
        }), 401
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'VIKRANTA API is running'}), 200
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Initialize sample data
        initialize_sample_data()
    
    print(f"🔍 Verifying socketio global: {socketio is not None}")
    
    return app, socketio  # Return both app and socketio

def initialize_sample_data():
    """Initialize sample geofences and test users"""
    from models.geofence import Geofence
    from models.user import User
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Polygon
    
    # Check if sample data already exists
    if Geofence.query.first() is None:
        # Sample geofences for major Indian cities
        sample_geofences = [
            {
                'name': 'Jaipur Old City - High Tourist Zone',
                'zone_type': 'tourist_area',
                'risk_level': 'medium',
                'coordinates': [[75.823, 26.919], [75.827, 26.919], [75.827, 26.923], [75.823, 26.923]],
                'description': 'Popular tourist area with high pickpocket reports'
            },
            {
                'name': 'Delhi Restricted Zone',
                'zone_type': 'restricted',
                'risk_level': 'high',
                'coordinates': [[77.200, 28.610], [77.205, 28.610], [77.205, 28.615], [77.200, 28.615]],
                'description': 'Government restricted area'
            },
            {
                'name': 'Mumbai Gateway Safe Zone',
                'zone_type': 'safe_zone',
                'risk_level': 'low',
                'coordinates': [[72.834, 18.921], [72.836, 18.921], [72.836, 18.923], [72.834, 18.923]],
                'description': 'Well-monitored tourist area with police presence'
            }
        ]
        
        for gf_data in sample_geofences:
            coords = gf_data['coordinates']
            # Close the polygon
            coords.append(coords[0])
            polygon = Polygon(coords)
            
            geofence = Geofence(
                name=gf_data['name'],
                zone_type=gf_data['zone_type'],
                risk_level=gf_data['risk_level'],
                polygon=from_shape(polygon, srid=4326),
                description=gf_data['description'],
                active=True
            )
            db.session.add(geofence)
        
        db.session.commit()
        print("Sample geofences created!")
    
    # Create main authority account if it doesn't exist
    if User.query.filter_by(email='admin@vikranta.gov.in').first() is None:
        from utils.auth_utils import hash_password
        
        main_authority = User(
            email='admin@vikranta.gov.in',
            name='Main Authority',
            phone='+911800111000',
            password_hash=hash_password('Admin@2025'),
            role='authority',
            is_verified=True
        )
        db.session.add(main_authority)
        db.session.commit()
        print("✅ Main Authority account created!")
        print("   Email: admin@vikranta.gov.in")
        print("   Password: Admin@2025")

if __name__ == '__main__':
    app, socketio = create_app()  # Unpack both app and socketio
    print("\n" + "="*60)
    print("🚀 VIKRANTA Backend Starting...")
    print(f"📡 Real-time WebSocket support: {'ENABLED' if socketio else 'DISABLED'}")
    print(f"✅ SocketIO instance: {type(socketio)}")
    print("👮 Authority alerts: ACTIVE")
    print("💬 Incident chat system: READY")
    print("="*60 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
