<!-- Improved README -->
<div align="center">

# VIKRANTA - AI Tourist Safety Companion

**A real-time, AI-powered safety and cultural guide for tourists, designed to provide peace of mind and enhance travel experiences.**

[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white)](https://www.twilio.com/)

</div>

---

**VIKRANTA** is a sophisticated web application that acts as a personal guardian for tourists. By leveraging real-time data, geospatial analysis, and AI, it offers a multi-faceted solution for modern travel challenges. From proactive safety alerts to an instant SOS system and a rich cultural guide, VIKRANTA ensures that tourists can explore with confidence.

The project features a decoupled architecture with a **React** frontend and a **Python (Flask)** backend, containerized with **Docker** for seamless development and deployment.

## ✨ Key Features

### For Tourists:
*   **Real-time Location Tracking:** See your live position on an interactive Mapbox map, ensuring you're always aware of your surroundings.
*   **AI-Powered Safety Score:** A dynamic safety score is calculated based on your location, time of day, and proximity to known geofenced zones (e.g., high-risk areas, safe zones).
*   **Proactive Geofence Alerts:** Receive automatic warnings when entering pre-defined high-risk or caution zones, providing timely safety advice.
*   **Emergency SOS System:**
    *   A one-click SOS button instantly sends a distress signal.
    *   Notifies a registered emergency contact via **SMS (powered by Twilio)**.
    *   Alerts a dedicated authority dashboard in real-time with the user's location.
*   **AI Cultural Guide:** Discover nearby cultural places and events with descriptions and safety tips, powered by the **Gemini AI**.
*   **Multi-Language Support:** The interface supports both English and Hindi.
*   **End-to-End Data Privacy:** An "End Journey" option securely deletes the user's account and all associated data.

### For Authorities:
*   **Centralized Incident Dashboard:** A real-time map view of all active tourists and ongoing SOS incidents.
*   **Instant Incident Alerts:** When a tourist triggers an SOS, their location immediately appears as a high-priority incident on the map.
*   **Real-time Chat & SMS Bridge:**
    *   Communicate directly with a tourist via a real-time chat interface.
    *   Chat messages from authorities are automatically relayed to the tourist as **SMS messages**, ensuring they receive updates even without an internet connection.
*   **Incident Lifecycle Management:** Authorities can acknowledge incidents and update their status (e.g., "En Route," "Resolved"), with updates sent to the tourist in real-time.

---

## 🛠️ Technology Stack

### Frontend
*   **Framework:** React.js (with Vite)
*   **Mapping:** Mapbox GL JS
*   **Real-time:** Socket.IO Client
*   **Styling:** Tailwind CSS
*   **HTTP Client:** Axios

### Backend
*   **Framework:** Flask (Python)
*   **Database:** PostgreSQL + PostGIS
*   **ORM:** SQLAlchemy + GeoAlchemy2
*   **Authentication:** Flask-JWT-Extended
*   **Real-time:** Flask-SocketIO
*   **SMS Service:** Twilio API
*   **Web Server:** Gunicorn

### Infrastructure & Deployment
*   **Containerization:** Docker & Docker Compose
*   **Deployment:** Railway.app (or any platform supporting Docker)

---

## 🚀 Getting Started

### Prerequisites
*   Docker and Docker Compose
*   Node.js and npm
*   Python and pip
*   Git

### Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd vikranta-mvp
    ```

2.  **Create the environment file:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and fill in the required API keys and secrets:
        ```
        # For backend/config.py
        DATABASE_URL=postgresql://user:password@db:5432/vikranta
        SECRET_KEY=your_super_secret_key
        GEMINI_API_KEY=your_gemini_api_key
        WEATHER_API_KEY=your_weather_api_key

        # For docker-compose.yml (Twilio credentials)
        TWILIO_ACCOUNT_SID=your_twilio_sid
        TWILIO_AUTH_TOKEN=your_twilio_auth_token
        TWILIO_PHONE_NUMBER=your_twilio_phone_number
        SMS_ENABLED=True
        ```

3.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```

4.  **Access the application:**
    *   **Frontend:** `http://localhost:3000`
    *   **Backend API:** `http://localhost:5000`

5.  **Initialize the database (first time only):**
    *   The `enable_postgis.py` script runs automatically on startup to set up the PostGIS extension.

---

## 📂 Project Structure

```
vikranta-mvp/
├── backend/
│   ├── models/         # SQLAlchemy database models
│   ├── routes/         # API endpoint definitions (Blueprints)
│   ├── utils/          # Utility functions (notifications, auth)
│   ├── app.py          # Main Flask application
│   ├── Dockerfile      # Backend Docker configuration
│   └── requirements.txt# Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── contexts/   # React contexts
│   │   ├── services/   # API services
│   │   ├── App.jsx     # Main React component
│   │   └── main.jsx    # Frontend entry point
│   ├── Dockerfile      # Frontend Docker configuration
│   └── package.json    # Node.js dependencies
│
├── .env                # Local environment variables (ignored by git)
├── .env.example        # Example environment file
└── docker-compose.yml  # Docker Compose configuration
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Deployment on Railway

The project is configured for automatic deployment on Railway from the `main` GitHub branch. The key settings for the backend service on Railway are:

*   **Build Method:** Dockerfile
*   **Dockerfile Path:** `./backend/Dockerfile`
*   **Start Command:** (Handled by the Dockerfile's `CMD` instruction)

This setup ensures that any push to the `main` branch will trigger a new build and deployment of the backend service.

### 🌐 Deployment Update
Initially, this project was deployed on **Railway**. However, due to the expiration of the free tier trial/credits, we have successfully migrated the application to **Render** to ensure 24/7 availability.

**New Deployment Link:** [https://thorough-reflection-production-1bb6.up.railway.app/](https://vikranta-frontend.onrender.com)

---

### 📋 Migration Summary
* **Original Host:** Railway (Free Tier Expired)
* **Current Host:** Render (Active)
* **Status:** ![Live](https://img.shields.io/badge/Status-Live-success)

> [!NOTE]
> **Cold Start:** Since we are now using Render's free tier, the application may take about 30–60 seconds to "wake up" during the initial load if the site has been inactive. We appreciate your patience!

---

### 🛠 Local Setup
If you prefer to run the project locally:
1. `git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git`
2. `npm install`
3. `npm start`
