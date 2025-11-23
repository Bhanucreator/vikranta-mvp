import os
import psycopg2
import json
from datetime import datetime

# Railway PostgreSQL connection
DATABASE_URL = os.getenv('DATABASE_URL') or 'postgresql://postgres:ybZwePsBHJIZyZZvOuSGmWqwxZJhbPzm@junction.proxy.rlwy.net:37634/railway'

# Bangalore safety zones
bangalore_zones = [
    {
        'name': 'MG Road - Commercial District',
        'zone_type': 'safe_zone',
        'risk_level': 'low',
        'description': 'Well-policed commercial area with high tourist traffic. Generally safe during day and evening.',
        'coordinates': [
            [77.5950, 12.9750],
            [77.6050, 12.9750],
            [77.6050, 12.9850],
            [77.5950, 12.9850],
            [77.5950, 12.9750]
        ]
    },
    {
        'name': 'Indiranagar - Residential Area',
        'zone_type': 'safe_zone',
        'risk_level': 'low',
        'description': 'Popular residential and nightlife area. Safe but be cautious of traffic.',
        'coordinates': [
            [77.6300, 12.9700],
            [77.6450, 12.9700],
            [77.6450, 12.9850],
            [77.6300, 12.9850],
            [77.6300, 12.9700]
        ]
    },
    {
        'name': 'Majestic Bus Stand Area',
        'zone_type': 'caution_zone',
        'risk_level': 'medium',
        'description': 'Crowded transport hub. High pickpocket activity. Keep belongings secure.',
        'coordinates': [
            [77.5700, 12.9750],
            [77.5800, 12.9750],
            [77.5800, 12.9800],
            [77.5700, 12.9800],
            [77.5700, 12.9750]
        ]
    },
    {
        'name': 'Koramangala - Tech Hub',
        'zone_type': 'safe_zone',
        'risk_level': 'low',
        'description': 'Tech startup hub with good infrastructure. Safe area with police presence.',
        'coordinates': [
            [77.6100, 12.9250],
            [77.6250, 12.9250],
            [77.6250, 12.9400],
            [77.6100, 12.9400],
            [77.6100, 12.9250]
        ]
    },
    {
        'name': 'Electronic City - Industrial Zone',
        'zone_type': 'caution_zone',
        'risk_level': 'medium',
        'description': 'Industrial area, less crowded at night. Use registered taxis after dark.',
        'coordinates': [
            [77.6600, 12.8400],
            [77.6750, 12.8400],
            [77.6750, 12.8550],
            [77.6600, 12.8550],
            [77.6600, 12.8400]
        ]
    }
]

def add_zones():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🗺️ Adding Bangalore safety zones...")
        
        for zone in bangalore_zones:
            # Create GeoJSON polygon
            polygon_geojson = {
                "type": "Polygon",
                "coordinates": [zone['coordinates']]
            }
            
            # Insert into database
            cur.execute("""
                INSERT INTO geofences (name, zone_type, risk_level, polygon_data, description, active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    zone_type = EXCLUDED.zone_type,
                    risk_level = EXCLUDED.risk_level,
                    polygon_data = EXCLUDED.polygon_data,
                    description = EXCLUDED.description,
                    updated_at = NOW()
            """, (
                zone['name'],
                zone['zone_type'],
                zone['risk_level'],
                json.dumps(polygon_geojson),
                zone['description'],
                True,
                datetime.utcnow()
            ))
            
            print(f"✅ Added: {zone['name']} ({zone['risk_level']})")
        
        conn.commit()
        print(f"\n🎉 Successfully added {len(bangalore_zones)} Bangalore zones!")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM geofences")
        total = cur.fetchone()[0]
        print(f"📊 Total geofences in database: {total}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_zones()
