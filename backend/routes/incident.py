from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from extensions import db
from models.user import User
from models.incident import Incident
from utils.notification import send_emergency_alert, send_sms
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

incident_bp = Blueprint('incident', __name__)

def emit_incident_alert(incident, user):
    """Emit real-time alert to all authorities via WebSocket"""
    print(f"📡 Attempting to emit incident alert for Incident #{incident.id}")
    try:
        from app import socketio
        print(f"📡 SocketIO object: {socketio}")
        if socketio:
            alert_data = {
                'incident_id': incident.id,
                'type': incident.type,
                'priority': incident.priority,
                'status': incident.status,
                'description': incident.description,
                'address': incident.address,
                'location': {
                    'latitude': incident.latitude,
                    'longitude': incident.longitude
                },
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone
                },
                'timestamp': incident.created_at.isoformat()
            }
            print(f"📡 Emitting to 'authorities' room: {alert_data}")
            socketio.emit('new_incident', alert_data, room='authorities')
            print(f"🚨 Real-time alert sent to authorities: Incident #{incident.id}")
        else:
            print(f"⚠️ SocketIO is None!")
    except Exception as e:
        print(f"⚠️ Could not emit WebSocket alert: {e}")
        traceback.print_exc()

@incident_bp.route('/panic', methods=['POST', 'OPTIONS'])
def trigger_panic():
    # Handle OPTIONS preflight request (no auth needed)
    if request.method == 'OPTIONS':
        return '', 200
    
    # For POST, verify JWT
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    try:
        incident = Incident(
            user_id=user_id,
            type='panic',
            status='active',
            priority='critical',
            latitude=data['latitude'],
            longitude=data['longitude'],
            address=data.get('address') or f"Location at {data['latitude']:.4f}, {data['longitude']:.4f}",
            description=data.get('description', 'Emergency panic button pressed')
        )
        db.session.add(incident)
        db.session.commit()
        
        print(f"🚨 Panic alert created: Incident #{incident.id} by user {user.name}")
        
        # Send SMS to the central emergency number
        try:
            emergency_number = current_app.config.get('EMERGENCY_CONTACT_NUMBER')
            if not emergency_number:
                raise ValueError("EMERGENCY_CONTACT_NUMBER is not configured in the application.")

            print(f"📱 Attempting to send SOS SMS to central emergency number: {emergency_number}")
            
            # Create the location string safely to avoid nested f-string issues
            lat = data.get("latitude")
            lon = data.get("longitude")
            location_str = incident.address or f"Lat: {lat}, Lon: {lon}"

            sms_message = (
                f"🚨 VIKRANTA SOS ALERT\n"
                f"User: {user.name} ({user.phone})\n"
                f"Location: {location_str}\n"
                f"Time: {datetime.now().strftime('%I:%M %p')}"
            )
            
            send_sms(emergency_number, sms_message)
            logger.info(f"📱 SOS SMS sent successfully to {emergency_number}")
            print(f"✅ SOS SMS sent successfully to {emergency_number}")

        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to send SOS SMS: {str(e)}")
            print(f"❌ CRITICAL: Failed to send SOS SMS: {str(e)}")
            # Return an error response because the primary notification failed
            return jsonify({'error': 'Failed to send emergency SMS notification.', 'details': str(e)}), 500        # Send real-time WebSocket alert to authorities
        emit_incident_alert(incident, user)
        
        return jsonify({
            'message': 'Emergency alert sent successfully',
            'incident_id': incident.id,
            'status': 'active',
            'priority': 'critical'
        }), 201
    except Exception as e:
        print(f"❌ Error creating panic incident: {e}")
        import traceback
        traceback.print_exc() # This will print the full error stack trace
        db.session.rollback()
        return jsonify({'error': 'Failed to create incident', 'details': str(e)}), 500

@incident_bp.route('/list', methods=['GET'])
@jwt_required()
def list_incidents():
    user_id = int(get_jwt_identity())  # Convert string back to int
    user = User.query.get(user_id)
    query = Incident.query
    if user.role != 'authority':
        query = query.filter_by(user_id=user_id)
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    incidents = query.order_by(Incident.created_at.desc()).all()
    incidents_data = []
    for incident in incidents:
        incident_dict = incident.to_dict()
        if user.role == 'authority':
            incident_user = User.query.get(incident.user_id)
            incident_dict['user'] = incident_user.to_dict() if incident_user else None
        incidents_data.append(incident_dict)
    return jsonify({'incidents': incidents_data, 'count': len(incidents_data)}), 200

@incident_bp.route('/<int:incident_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_incident(incident_id):
    """Authority responds to an incident"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'authority':
        return jsonify({'error': 'Only authorities can respond to incidents'}), 403
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')  # acknowledged, en_route, resolved
    response_message = data.get('message', '')
    
    if new_status:
        incident.status = new_status
        incident.updated_at = datetime.now()
    
    db.session.commit()
    
    # Get tourist information for notifications
    tourist = User.query.get(incident.user_id)
    
    # Notify tourist via WebSocket
    try:
        from app import socketio
        if socketio:
            notification_data = {
                'incident_id': incident.id,
                'status': new_status,
                'message': response_message,
                'authority_name': user.name,
                'timestamp': datetime.now().isoformat()
            }
            room = f'user_{incident.user_id}'
            print(f"📡 Attempting to emit incident_update to room: {room}")
            print(f"📡 Notification data: {notification_data}")
            socketio.emit('incident_update', notification_data, room=room)
            print(f"✅ WebSocket status update sent to tourist room: {room}")
    except Exception as e:
        print(f"⚠️ Could not emit status update: {e}")
        import traceback
        traceback.print_exc()
    
    # Send SMS notification to tourist
    try:
        print(f"📱 Attempting to send status SMS to tourist: {tourist.name if tourist else 'Unknown'}")
        status_messages = {
            'acknowledged': f"🚨 VIKRANTA: Authority {user.name} has ACKNOWLEDGED your emergency alert. Help is on the way!",
            'en_route': f"🚑 VIKRANTA: Authority {user.name} is EN ROUTE to your location. Stay calm and stay safe!",
            'resolved': f"✅ VIKRANTA: Your emergency has been marked as RESOLVED by {user.name}. Stay safe!"
        }
        
        sms_text = status_messages.get(new_status, f"VIKRANTA: Status update - {new_status}")
        if response_message:
            sms_text += f"\nMessage: {response_message}"
        
        if tourist and tourist.phone:
            print(f"📱 Sending notification to {tourist.phone}: {sms_text[:50]}...")
            sms_result = send_sms(tourist.phone, sms_text)
            if sms_result:
                logger.info(f"📱 Status notification sent to tourist {tourist.name} ({new_status})")
                print(f"✅ Status notification delivered (SMS/In-app)")
            # Note: send_sms returns True even for trial account (graceful handling)
        else:
            print(f"⚠️ Tourist phone not available. Tourist: {tourist}, Phone: {tourist.phone if tourist else 'N/A'}")
            logger.warning(f"Tourist phone not available for incident {incident_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send status SMS: {str(e)}")
        print(f"❌ Exception sending status SMS: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return jsonify({
        'message': 'Response recorded successfully',
        'incident': incident.to_dict()
    }), 200

@incident_bp.route('/<int:incident_id>', methods=['GET'])
@jwt_required()
def get_incident_details(incident_id):
    """Get detailed information about a specific incident"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Check permissions
    if user.role != 'authority' and incident.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident_dict = incident.to_dict()
    
    # Add user info for authorities
    if user.role == 'authority':
        tourist = User.query.get(incident.user_id)
        incident_dict['user'] = tourist.to_dict() if tourist else None
    
    return jsonify({'incident': incident_dict}), 200

@incident_bp.route('/<int:incident_id>/send-message', methods=['POST'])
@jwt_required()
def send_quick_message(incident_id):
    """Authority sends a quick message to tourist with SMS notification"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'authority':
        return jsonify({'error': 'Only authorities can send quick messages'}), 403
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get tourist information
    tourist = User.query.get(incident.user_id)
    
    # Send SMS notification to tourist
    try:
        print(f"📱 Attempting to send quick message to tourist: {tourist.name if tourist else 'Unknown'}")
        sms_text = f"🚨 VIKRANTA - Authority {user.name}:\n{message}"
        
        if tourist and tourist.phone:
            print(f"📱 Sending notification to {tourist.phone}: {sms_text[:50]}...")
            sms_result = send_sms(tourist.phone, sms_text)
            if sms_result:
                logger.info(f"📱 Quick message notification sent to tourist {tourist.name}")
                print(f"✅ Quick message notification delivered (SMS/In-app)")
            # Note: send_sms returns True even for trial account (graceful handling)
        else:
            print(f"⚠️ Tourist phone not available for incident {incident_id}")
            logger.warning(f"⚠️ Tourist phone not available for incident {incident_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send quick message SMS: {str(e)}")
        print(f"❌ Exception sending quick message SMS: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't fail the request if SMS fails
    
    # WebSocket notification - send to both incident room AND tourist's personal room
    try:
        from app import socketio
        if socketio:
            message_data = {
                'incident_id': incident.id,
                'message': message,
                'sender_name': user.name,
                'sender_role': 'authority',
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to incident room (for chat)
            socketio.emit('new_message', message_data, room=f'incident_{incident.id}')
            print(f"✅ WebSocket message sent to incident room: incident_{incident.id}")
            
            # Send to tourist's personal room (for notification)
            tourist_room = f'user_{incident.user_id}'
            socketio.emit('quick_message_notification', {
                'incident_id': incident.id,
                'message': message,
                'authority_name': user.name,
                'timestamp': datetime.now().isoformat()
            }, room=tourist_room)
            print(f"✅ WebSocket notification sent to tourist room: {tourist_room}")
    except Exception as e:
        print(f"⚠️ Could not emit WebSocket message: {e}")
        import traceback
        traceback.print_exc()
    
    return jsonify({
        'message': 'Quick message sent successfully',
        'sms_sent': tourist and tourist.phone is not None
    }), 200
