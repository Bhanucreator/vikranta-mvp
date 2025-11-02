import bcrypt
import random
import string
from datetime import datetime, timedelta

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def is_otp_valid(otp_created_at, expiry_minutes=10):
    """Check if OTP is still valid"""
    if not otp_created_at:
        return False
    expiry_time = otp_created_at + timedelta(minutes=expiry_minutes)
    return datetime.utcnow() < expiry_time
