# VIKRANTA - Smart Tourist Safety & Incident Response System

## Overview
VIKRANTA is a comprehensive tourist safety platform built for Smart India Hackathon 2025. The system provides real-time location tracking, geo-fence warnings, emergency panic buttons, and an authority dashboard for incident management.

## Features
- **User Registration & Authentication**: Email + OTP verification
- **Profile Management**: Travel itinerary and personal information
- **Live Location Tracking**: Real-time GPS tracking with Mapbox
- **Panic Button**: Emergency alert system with location sharing
- **Geo-fence Warnings**: Polygon-based zone alerts
- **Authority Dashboard**: Incident monitoring and dispatch management
- **Notifications**: Push/SMS/Email alerts (stubbed in MVP)

## Tech Stack
- **Frontend**: React 18 + Vite + Tailwind CSS + React Router + Mapbox GL JS
- **Backend**: Python Flask + Flask-RESTful + SQLAlchemy
- **Database**: PostgreSQL with PostGIS extension
- **Deployment**: Docker + docker-compose

## Prerequisites
- Docker and Docker Compose installed
- Mapbox API token (get free at mapbox.com)

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd vikranta-mvp
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your Mapbox token and other configurations
```

### 3. Build and run with Docker
```bash
docker-compose up --build
```

### 4. Access the application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api
- Database: localhost:5432

## Test User Accounts
- Tourist: tourist@vikranta.com / password123
- Authority: authority@vikranta.com / admin123

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-otp` - OTP verification

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update profile
- `POST /api/user/itinerary` - Create/update itinerary

### Location Services
- `POST /api/location/update` - Update user location
- `GET /api/location/track/:user_id` - Track user location

### Incident Management
- `POST /api/incident/panic` - Trigger panic alert
- `GET /api/incident/list` - List all incidents
- `PUT /api/incident/:id/status` - Update incident status

### Geofencing
- `GET /api/geofence/list` - List all geofences
- `POST /api/geofence/check` - Check if location in geofence

## License
MIT License - Built for Smart India Hackathon 2025
