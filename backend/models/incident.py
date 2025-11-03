from extensions import db
from datetime import datetime
try:
    from geoalchemy2 import Geometry
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    POSTGIS_AVAILABLE = True
except ImportError:
    POSTGIS_AVAILABLE = False

class Incident(db.Model):
    """Incident/Emergency model"""
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Incident details
    type = db.Column(db.String(50), nullable=False)  # panic, medical, theft, etc.
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved, false_alarm
    priority = db.Column(db.String(20), default='high')  # low, medium, high, critical
    
    # Location - Use fallback if PostGIS not available
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(255))
    
    # Details
    description = db.Column(db.Text)
    responder_notes = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert incident to dictionary"""
        location_data = None
        if self.latitude is not None and self.longitude is not None:
            location_data = {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'location': location_data,
            'address': self.address,
            'description': self.description,
            'responder_notes': self.responder_notes,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<Incident {self.id} - {self.type}>'
