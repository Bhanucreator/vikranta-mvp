"""Flask extensions initialization"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail

# Initialize extensions (no app yet)
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
