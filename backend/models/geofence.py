from extensions import db
from datetime import datetime
try:
    from geoalchemy2 import Geometry
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    POSTGIS_AVAILABLE = True
except ImportError:
    POSTGIS_AVAILABLE = False

class Geofence(db.Model):
    """Geofence/Zone model"""
    __tablename__ = 'geofences'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    zone_type = db.Column(db.String(50), nullable=False)  # restricted, high_crime, cultural, safe_zone
    risk_level = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Simplified polygon storage (JSON text for now)
    polygon_data = db.Column(db.Text)  # Store GeoJSON as text
    
    # Details
    description = db.Column(db.Text)
    warning_message = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert geofence to dictionary"""
        import json
        polygon_data = None
        if self.polygon_data:
            try:
                polygon_data = json.loads(self.polygon_data)
            except:
                pass
        
        return {
            'id': self.id,
            'name': self.name,
            'zone_type': self.zone_type,
            'risk_level': self.risk_level,
            'polygon': polygon_data,
            'description': self.description,
            'warning_message': self.warning_message,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Geofence {self.name}>'
