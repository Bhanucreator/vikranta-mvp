# backend/utils/fallback_data.py

def get_fallback_cultural_places():
    """
    Returns a list of fallback cultural places for demonstration purposes.
    This is used when the Gemini API is unavailable or rate-limited.
    """
    return [
        {
            "name": "Bangalore Palace",
            "type": "Historic Palace",
            "about": "An exemplary of royal grandeur, Bangalore Palace was built in 1878. It is a mix of Tudor and Scottish Gothic architecture.",
            "latitude": 12.9988,
            "longitude": 77.5921,
            "safety_level": "safe",
            "rating": 4.4,
            "dress_code": "Casual and respectful",
            "opening_hours": "10:00 AM - 5:30 PM",
            "entry_fee": "₹230 for Indians, ₹460 for Foreigners",
            "best_time": "Afternoons",
            "safety_tips": "Beware of unofficial guides. Stick to the designated tour paths.",
            "etiquette": "Do not touch the exhibits. Photography may have extra charges.",
            "languages_spoken": "English, Hindi, Kannada",
            "emergency_contact": "100"
        },
        {
            "name": "Lalbagh Botanical Garden",
            "type": "Botanical Garden",
            "about": "A nationally and internationally renowned centre for botanical artwork, scientific study of plants and also conservation of plants.",
            "latitude": 12.9507,
            "longitude": 77.5848,
            "safety_level": "safe",
            "rating": 4.5,
            "dress_code": "Comfortable walking attire",
            "opening_hours": "6:00 AM - 7:00 PM",
            "entry_fee": "₹25 per person",
            "best_time": "Early morning or late afternoon",
            "safety_tips": "Stay on marked paths. The garden is large, so keep track of your location.",
            "etiquette": "Do not pluck flowers or disturb the plants. Keep the area clean.",
            "languages_spoken": "English, Kannada",
            "emergency_contact": "100"
        },
        {
            "name": "Tipu Sultan's Summer Palace",
            "type": "Historic Site",
            "about": "An example of Indo-Islamic architecture, this was the summer residence of the Mysorean ruler Tipu Sultan.",
            "latitude": 12.9592,
            "longitude": 77.5736,
            "safety_level": "safe",
            "rating": 4.2,
            "dress_code": "Respectful attire",
            "opening_hours": "8:30 AM - 5:30 PM",
            "entry_fee": "₹20 for Indians, ₹200 for Foreigners",
            "best_time": "Anytime during open hours",
            "safety_tips": "Watch your step on the old wooden structure.",
            "etiquette": "Maintain silence and respect the historical significance of the palace.",
            "languages_spoken": "English, Hindi, Kannada",
            "emergency_contact": "100"
        },
        {
            "name": "Visvesvaraya Industrial & Technological Museum",
            "type": "Museum",
            "about": "A museum dedicated to the memory of Sir M. Visvesvaraya. It houses various technical inventions and offers a glimpse into the history of technology.",
            "latitude": 12.9767,
            "longitude": 77.5983,
            "safety_level": "safe",
            "rating": 4.6,
            "dress_code": "Casual",
            "opening_hours": "9:30 AM - 6:00 PM",
            "entry_fee": "₹75 per person",
            "best_time": "Weekdays to avoid crowds",
            "safety_tips": "Follow the instructions for interactive exhibits.",
            "etiquette": "Supervise children closely. Do not run inside the museum.",
            "languages_spoken": "English, Kannada",
            "emergency_contact": "100"
        }
    ]
