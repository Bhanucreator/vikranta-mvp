import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# --- Environment Detection ---
# Detects if the app is running in a production environment like Railway.
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') is not None or \
                os.environ.get('FLASK_ENV') == 'production'

class Config:
    """Base configuration with security best practices."""

    # --- Critical Security: Secret Keys ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY

    # In production, these keys MUST be set. The app will fail to start otherwise.
    if IS_PRODUCTION and (not SECRET_KEY or not JWT_SECRET_KEY):
        raise ValueError("FATAL: SECRET_KEY and JWT_SECRET_KEY must be set in the production environment.")

    # --- Database Configuration ---
    database_url = os.environ.get('DATABASE_URL')
    if IS_PRODUCTION and not database_url:
        raise ValueError("FATAL: DATABASE_URL must be set in the production environment.")
    
    # Fix for Railway's 'postgres://' prefix
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- JWT Timing ---
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # --- Email Configuration ---
    MAIL_SERVER = os.environ.get('SMTP_SERVER')
    MAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('SMTP_USERNAME')
    MAIL_PASSWORD = os.environ.get('SMTP_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    MAIL_SUPPRESS_SEND = False

    # --- Twilio SMS Configuration ---
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    SMS_ENABLED = os.environ.get('SMS_ENABLED', 'false').lower() == 'true'

    # --- Application Settings ---
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    OTP_EXPIRY_MINUTES = 10
    MAX_LOGIN_ATTEMPTS = 5

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    TESTING = False
    
    # Use insecure defaults for local development if not set
    if not Config.SECRET_KEY:
        print("WARNING: Using insecure default SECRET_KEY for development.")
        SECRET_KEY = 'dev-secret-key-insecure'
    if not Config.JWT_SECRET_KEY:
        print("WARNING: Using insecure default JWT_SECRET_KEY for development.")
        JWT_SECRET_KEY = 'jwt-secret-key-insecure'
    
    if not Config.SQLALCHEMY_DATABASE_URI:
        print("WARNING: Using default local PostgreSQL database for development.")
        SQLALCHEMY_DATABASE_URI = 'postgresql://vikranta_user:vikranta_pass@localhost:5432/vikranta_db'

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False
    # All critical variables are already enforced in the base Config class for production.

class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Use simple, non-random keys for predictable testing
    SECRET_KEY = 'testing-secret-key'
    JWT_SECRET_KEY = 'testing-jwt-secret-key'
    SMS_ENABLED = False
    MAIL_SUPPRESS_SEND = True

# Dictionary to access config classes by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
