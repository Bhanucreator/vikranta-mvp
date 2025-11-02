from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User, Itinerary
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())  # Convert string back to int
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    itineraries = [it.to_dict() for it in user.itineraries.all()]
    profile_data = user.to_dict()
    profile_data['itineraries'] = itineraries
    return jsonify(profile_data), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())  # Convert string back to int
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    allowed_fields = ['name', 'phone', 'emergency_contact', 'medical_info', 'profile_image']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully', 'user': user.to_dict()}), 200

@user_bp.route('/itinerary', methods=['POST'])
@jwt_required()
def create_itinerary():
    user_id = int(get_jwt_identity())  # Convert string back to int
    data = request.get_json()
    required_fields = ['destination', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    itinerary = Itinerary(
        user_id=user_id,
        destination=data['destination'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        activities=data.get('activities'),
        accommodation=data.get('accommodation'),
        notes=data.get('notes')
    )
    db.session.add(itinerary)
    db.session.commit()
    return jsonify({'message': 'Itinerary created successfully', 'itinerary': itinerary.to_dict()}), 201

@user_bp.route('/itinerary/<int:itinerary_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_itinerary(itinerary_id):
    user_id = int(get_jwt_identity())  # Convert string back to int
    itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=user_id).first()
    if not itinerary:
        return jsonify({'error': 'Itinerary not found'}), 404
    if request.method == 'GET':
        return jsonify(itinerary.to_dict()), 200
    elif request.method == 'DELETE':
        db.session.delete(itinerary)
        db.session.commit()
        return jsonify({'message': 'Itinerary deleted successfully'}), 200
    return jsonify({'message': 'Method not allowed'}), 405

@user_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Delete tourist account and all associated data when journey ends
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        print(f"[User] Deleting account for user {user_id}: {user.email}")
        
        # Delete all associated data (cascade should handle this, but being explicit)
        # Delete user locations
        from models.user import UserLocation
        UserLocation.query.filter_by(user_id=user_id).delete()
        
        # Delete itineraries
        Itinerary.query.filter_by(user_id=user_id).delete()
        
        # Delete incidents reported by user (correct field name is user_id)
        from models.incident import Incident
        Incident.query.filter_by(user_id=user_id).delete()
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        print(f"[User] ✅ Account deleted successfully for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Journey ended. Account and all data deleted successfully.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[User] ❌ Error deleting account: {str(e)}")
        return jsonify({'error': 'Failed to delete account', 'details': str(e)}), 500
