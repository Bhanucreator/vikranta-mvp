from .auth import auth_bp
from .user import user_bp
from .location import location_bp
from .incident import incident_bp
from .geofence import geofence_bp

__all__ = ['auth_bp', 'user_bp', 'location_bp', 'incident_bp', 'geofence_bp']
