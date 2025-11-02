from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from utils.auth_utils import hash_password, verify_password, generate_otp, is_otp_valid
from utils.notification import send_otp_email
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user (tourists only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'name', 'password', 'emergency_contact']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Only tourists can register through this endpoint
        role = data.get('role', 'tourist')
        if role != 'tourist':
            return jsonify({'error': 'Only tourists can register. Authorities are added by admin.'}), 403
        
        # Validate email format
        try:
            valid = validate_email(data['email'])
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Generate OTP
        otp = generate_otp()
        
        # Create new user
        user = User(
            email=email,
            name=data['name'],
            phone=data.get('phone'),
            emergency_contact=data['emergency_contact'],
            password_hash=hash_password(data['password']),
            role='tourist',  # Force tourist role
            otp=otp,
            otp_created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send OTP via email
        email_sent = False
        try:
            email_sent = send_otp_email(email, otp, data['name'])
            if email_sent:
                print(f"✅ OTP email sent successfully to {email}")
            else:
                print(f"⚠️  Email sending failed for {email}")
        except Exception as email_error:
            print(f"❌ Email error: {str(email_error)}")
        
        # Log OTP to console for development (remove in production)
        print(f"🔐 OTP for {email}: {otp}")
        
        return jsonify({
            'message': 'Registration successful. Please check your email for OTP.',
            'user_id': user.id,
            'email_sent': email_sent
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and activate user account"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'otp' not in data:
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        # Check OTP validity
        if user.otp != data['otp']:
            return jsonify({'error': 'Invalid OTP'}), 400
        
        if not is_otp_valid(user.otp_created_at):
            return jsonify({'error': 'OTP has expired. Please request a new one.'}), 400
        
        # Verify user
        user.is_verified = True
        user.otp = None
        user.otp_created_at = None
        db.session.commit()
        
        # Generate JWT token (identity must be string)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Email verified successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not verify_password(data['password'], user.password_hash):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_verified:
            return jsonify({'error': 'Please verify your email first'}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token (identity must be string)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user email"""
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        # Generate new OTP
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = datetime.utcnow()
        db.session.commit()
        
        # Send OTP
        send_otp_email(user.email, otp, user.name)
        
        return jsonify({'message': 'OTP sent successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = int(get_jwt_identity())  # Convert string back to int
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/add-authority', methods=['POST'])
@jwt_required()
def add_authority():
    """Add a new authority user (only accessible by existing authority)"""
    try:
        # Get current user
        user_id = int(get_jwt_identity())  # Convert string back to int
        current_user = User.query.get(user_id)
        
        if not current_user or current_user.role != 'authority':
            return jsonify({'error': 'Only authorities can add new authority users'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'name', 'password', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        try:
            valid = validate_email(data['email'])
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new authority user (no OTP verification needed)
        new_authority = User(
            email=email,
            name=data['name'],
            phone=data['phone'],
            password_hash=hash_password(data['password']),
            role='authority',
            is_verified=True  # Authority users are pre-verified
        )
        
        db.session.add(new_authority)
        db.session.commit()
        
        return jsonify({
            'message': 'Authority user created successfully',
            'user': new_authority.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

