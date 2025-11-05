"""
Script to add Bangalore geofences via API endpoint
Run this after deploying the create_bangalore_zones endpoint
"""
import requests
import json

# Backend API URL
API_URL = 'https://vikranta-mvp-production.up.railway.app/api'

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
    print("🗺️ Adding Bangalore safety zones via API...")
    
    response = requests.post(
        f'{API_URL}/geofence/create-bangalore-zones',
        json={'zones': bangalore_zones},
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✅ Zones added successfully!")
        print(response.json())
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    add_zones()
