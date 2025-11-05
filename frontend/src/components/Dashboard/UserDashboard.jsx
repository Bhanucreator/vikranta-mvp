import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation } from '../../contexts/LocationContext';
import Map, { Marker, Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import api from '../../services/api';
import { io } from 'socket.io-client';
import { toast } from 'react-toastify';

export default function UserDashboard() {
  const { user, logout } = useAuth();
  const { currentLocation, setCurrentLocation, setTracking } = useLocation();
  const [showProfileSidebar, setShowProfileSidebar] = useState(false);
  const [activeView, setActiveView] = useState('dashboard');
  const [safetyScore, setSafetyScore] = useState(9.0);
  const [emergencyActive, setEmergencyActive] = useState(false);
  const [nearbyPlaces, setNearbyPlaces] = useState([]);
  const [safetyZones, setSafetyZones] = useState([]);
  const [geofences, setGeofences] = useState([]); // Raw geofence data for map rendering
  const [geofenceAlerts, setGeofenceAlerts] = useState([]);
  const [language, setLanguage] = useState('en');
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const [culturalDetails, setCulturalDetails] = useState(null);
  const [weather, setWeather] = useState({ temp: '--', description: 'Loading...', icon: '🌤️' });
  const [culturalEvent, setCulturalEvent] = useState({ name: 'Loading...', date: '' });
  const [showEndJourneyModal, setShowEndJourneyModal] = useState(false);
  const [incidentStatus, setIncidentStatus] = useState(null);
  const [showStatusNotification, setShowStatusNotification] = useState(false);
  const socketRef = useRef(null);
  const lastCulturalFetchRef = useRef(null); // Track last fetch time
  const culturalCacheRef = useRef(null); // Cache cultural data
  const lastPlacesFetchRef = useRef(null); // Track last places fetch
  const placesCacheRef = useRef(null); // Cache places data
  const lastZonesGenerateRef = useRef(null); // Track last zones generation
  
  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoidmlrcmFudGEiLCJhIjoiY2xrbTJuMzJ5MDFvYjNlbzh4YnZ5YnpoYyJ9.placeholder';
  // Use Railway backend URL for WebSocket connection
  const BACKEND_URL = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || 
                       import.meta.env.VITE_API_URL?.replace('/api', '') || 
                       'http://localhost:5000';
  
  // Language translations
  const translations = {
    en: {
      dashboard: 'Dashboard',
      map: 'Map',
      cultural: 'Cultural',
      sos: 'SOS',
      emergency: 'Emergency',
      safetyScore: 'Safety Score',
      profile: 'Profile',
      logout: 'Logout',
      getDirections: 'Get Directions',
      details: 'Details',
      offlineMode: 'Offline Mode',
    },
    hi: {
      dashboard: 'डैशबोर्ड',
      map: 'नक्शा',
      cultural: 'सांस्कृतिक',
      sos: 'एसओएस',
      emergency: 'आपातकाल',
      safetyScore: 'सुरक्षा स्कोर',
      profile: 'प्रोफ़ाइल',
      logout: 'लॉग आउट',
      getDirections: 'दिशा निर्देश',
      details: 'विवरण',
      offlineMode: 'ऑफ़लाइन मोड',
    },
  };
  
  const t = (key) => translations[language]?.[key] || translations.en[key];
  
  // Offline mode detection
  useEffect(() => {
    const handleOnline = () => setIsOfflineMode(false);
    const handleOffline = () => setIsOfflineMode(true);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    setIsOfflineMode(!navigator.onLine);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  useEffect(() => {
    setTracking(true);
    fetchNearbyPlaces(); // Now async, will fetch from Gemini AI
    fetchSafetyZones();
    checkGeofences();
    startRealTimeLocationTracking();
    initializeWebSocket(); // Initialize WebSocket for real-time notifications
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    if (currentLocation) {
      fetchNearbyPlaces(); // Refresh cultural places when location changes
      fetchSafetyZones(); // Refresh nearby safety zones based on location
      fetchWeather(); // Fetch real-time weather
      fetchCulturalEvent(); // Fetch local cultural events
      checkGeofences();
      calculateSafetyScore();
      sendLocationToBackend();
    }
  }, [currentLocation]);
  
  // Real-time location tracking using browser geolocation API
  const startRealTimeLocationTracking = () => {
    console.log('🌍 Starting real-time location tracking...');
    
    if ('geolocation' in navigator) {
      console.log('✅ Geolocation API available');
      
      const watchId = navigator.geolocation.watchPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          console.log('📍 Location updated:', { latitude, longitude, accuracy });
          
          // Log accuracy information
          if (accuracy > 100) {
            console.warn('⚠️ Location accuracy is low:', accuracy, 'meters. Consider:');
            console.warn('   1. Moving to an open area for better GPS signal');
            console.warn('   2. Ensuring GPS is enabled in device settings');
            console.warn('   3. Waiting a few seconds for GPS to get better fix');
          } else if (accuracy < 20) {
            console.log('✅ Excellent GPS accuracy:', accuracy, 'meters');
          } else if (accuracy < 50) {
            console.log('✅ Good GPS accuracy:', accuracy, 'meters');
          }
          
          setCurrentLocation({
            latitude,
            longitude,
            accuracy,
            timestamp: new Date().toISOString()
          });
        },
        (error) => {
          console.error('❌ Geolocation error:', error);
          console.error('Error code:', error.code, 'Message:', error.message);
          
          if (error.code === 1) {
            toast.error('🚫 Location permission denied! Please enable location access in your browser settings.');
          } else if (error.code === 2) {
            toast.warning('⚠️ Location unavailable! Checking device GPS settings...');
          } else if (error.code === 3) {
            console.warn('⏱️ GPS timeout - will retry with lower accuracy for faster response');
            // Don't show alert, just retry with lower accuracy
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 60000, // Increased to 60 seconds for slower GPS
          maximumAge: 10000 // Allow 10 second old location to prevent constant timeouts
        }
      );
      
      // Also try to get an immediate position with fallback strategy
      // First try with lower accuracy (faster response)
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          console.log('📍 Initial position obtained:', { latitude, longitude, accuracy: `${accuracy.toFixed(0)}m` });
          setCurrentLocation({
            latitude,
            longitude,
            accuracy,
            timestamp: new Date().toISOString()
          });
          toast.success(`📍 Location acquired (±${accuracy.toFixed(0)}m accuracy)`);
        },
        (error) => {
          console.warn('⚠️ Initial position timeout, watchPosition will continue trying...');
          toast.info('🔄 Getting your location... This may take a moment.');
        },
        {
          enableHighAccuracy: false, // Start with low accuracy for faster initial fix
          timeout: 10000, // Quick 10 second timeout for initial position
          maximumAge: 30000 // Allow 30 second old location for initial display
        }
      );
      
      // Cleanup function to stop watching when component unmounts
      return () => {
        console.log('🛑 Stopping location tracking');
        navigator.geolocation.clearWatch(watchId);
      };
    } else {
      console.error('❌ Geolocation not supported by this browser');
      alert('🚫 Your browser does not support geolocation!\n\nPlease use a modern browser like Chrome, Firefox, or Edge to access VIKRANTA.');
    }
  };
  
  // Initialize WebSocket for real-time authority notifications
  const initializeWebSocket = () => {
    // Configure Socket.IO with better error handling and transport options
    socketRef.current = io(BACKEND_URL, {
      transports: ['polling', 'websocket'], // Try polling first, then websocket
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000,
    });
    
    socketRef.current.on('connect', () => {
      console.log('🔌 Tourist connected to WebSocket');
      console.log('👤 User data:', user);
      // Join user-specific room
      if (user?.id) {
        console.log(`📡 Emitting join_user_room with user_id: ${user.id}`);
        socketRef.current.emit('join_user_room', { user_id: user.id });
      } else {
        console.warn('⚠️ User ID not available, cannot join personal room');
      }
    });
    
    socketRef.current.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error.message);
      console.log('🔄 Will retry connection...');
    });
    
    socketRef.current.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected to WebSocket (attempt ${attemptNumber})`);
      // Re-join room after reconnection
      if (user?.id) {
        socketRef.current.emit('join_user_room', { user_id: user.id });
      }
    });
    
    socketRef.current.on('reconnect_failed', () => {
      console.error('❌ Failed to reconnect to WebSocket after multiple attempts');
    });
    
    // Confirmation that we joined the room
    socketRef.current.on('joined_user_room', (data) => {
      console.log('✅ Successfully joined user room:', data);
    });
    
    socketRef.current.on('incident_update', (data) => {
      console.log('📢 Incident update received:', data);
      
      // Update incident status
      setIncidentStatus({
        status: data.status,
        message: data.message,
        authority_name: data.authority_name,
        timestamp: data.timestamp
      });
      
      // Show notification
      setShowStatusNotification(true);
      
      // Show toast notification
      const statusEmoji = data.status === 'acknowledged' ? '👀' : 
                         data.status === 'en_route' ? '🚓' : '✅';
      
      toast.info(`${statusEmoji} ${data.message}`, {
        autoClose: 8000,
        position: 'top-center'
      });
      
      // Auto-hide notification after 10 seconds
      setTimeout(() => {
        setShowStatusNotification(false);
      }, 10000);
    });
    
    // Listen for quick messages from authorities
    socketRef.current.on('quick_message_notification', (data) => {
      console.log('💬 Quick message received:', data);
      
      // Show toast notification
      toast.info(`💬 Message from ${data.authority_name}: ${data.message}`, {
        autoClose: 10000,
        position: 'top-center'
      });
      
      // You can also update state to show in UI
      setIncidentStatus({
        status: 'message',
        message: data.message,
        authority_name: data.authority_name,
        timestamp: data.timestamp
      });
      setShowStatusNotification(true);
      
      setTimeout(() => {
        setShowStatusNotification(false);
      }, 10000);
    });
    
    socketRef.current.on('disconnect', () => {
      console.log('🔌 Tourist disconnected from WebSocket');
    });
  };
  
  // Send location updates to backend for tracking
  const sendLocationToBackend = async () => {
    if (!currentLocation) return;
    
    try {
      await api.post('/location/update', {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        accuracy: currentLocation.accuracy,
        timestamp: currentLocation.timestamp
      });
    } catch (error) {
      // Silently fail - location tracking continues even if backend update fails
      console.error('Location update error:', error);
    }
  };
  
  // Geofencing - Location-based safety alerts
  const checkGeofences = async () => {
    if (!currentLocation) return;
    
    try {
      // Real API call to backend geofence check
      const response = await api.post('/geofence/check', {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude
      });
      
      const { inside_geofences } = response.data;
      
      if (inside_geofences && inside_geofences.length > 0) {
        const alerts = inside_geofences.map(zone => ({
          id: zone.id,
          message: `⚠️ Warning: You are in ${zone.name} (${zone.alert_type || 'safety zone'})`,
          severity: zone.severity || 'warning',
        }));
        setGeofenceAlerts(alerts);
      } else {
        setGeofenceAlerts([]);
      }
    } catch (error) {
      console.error('Geofence check error:', error);
      // Fallback to local geofence check if API fails
      const alerts = [];
      const dangerZones = [
        { name: 'Construction Area', lat: 26.9200, lng: 75.8100, radius: 0.5 },
        { name: 'Traffic Congestion', lat: 26.9180, lng: 75.8150, radius: 0.3 },
      ];
      
      dangerZones.forEach(zone => {
        const distance = calculateDistance(
          currentLocation.latitude,
          currentLocation.longitude,
          zone.lat,
          zone.lng
        );
        
        if (distance <= zone.radius) {
          alerts.push({
            id: zone.name,
            message: `⚠️ Warning: You are near ${zone.name}`,
            severity: 'warning',
          });
        }
      });
      
      setGeofenceAlerts(alerts);
    }
  };
  
  // Calculate distance between two points (Haversine formula)
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };
  
  // AI-based Safety Score calculation
  const calculateSafetyScore = () => {
    if (!currentLocation) {
      setSafetyScore(9.0); // Default score when no location
      return;
    }
    
    // Calculate safety score based on ACTUAL geofence data
    let score = 10; // Start with perfect score
    
    // Factor 1: Time of day (6 AM - 8 PM is safer)
    const timeOfDay = new Date().getHours();
    const isSafeTime = timeOfDay >= 6 && timeOfDay <= 20;
    if (!isSafeTime) {
      score -= 1.5; // Reduce score at night
      console.log('🌙 Night time detected: -1.5 points');
    }
    
    // Factor 2: Geofence alerts (most important factor)
    const highRiskAlerts = geofenceAlerts.filter(alert => alert.risk === 'high');
    const mediumRiskAlerts = geofenceAlerts.filter(alert => alert.risk === 'medium');
    
    if (highRiskAlerts.length > 0) {
      score -= highRiskAlerts.length * 3; // -3 points per high-risk zone
      console.log(`🚨 In ${highRiskAlerts.length} high-risk zone(s): -${highRiskAlerts.length * 3} points`);
    }
    
    if (mediumRiskAlerts.length > 0) {
      score -= mediumRiskAlerts.length * 1.5; // -1.5 points per caution zone
      console.log(`⚠️ In ${mediumRiskAlerts.length} caution zone(s): -${mediumRiskAlerts.length * 1.5} points`);
    }
    
    // Factor 3: Nearby safe zones (positive factor)
    const safeZonesNearby = safetyZones.filter(zone => 
      zone.safety === 'High Safety' && zone.distance < 2
    ).length;
    
    if (safeZonesNearby > 0) {
      score += Math.min(safeZonesNearby * 0.5, 1.5); // +0.5 per safe zone, max +1.5
      console.log(`✅ ${safeZonesNearby} safe zone(s) nearby: +${Math.min(safeZonesNearby * 0.5, 1.5)} points`);
    }
    
    // Clamp score between 0 and 10
    const finalScore = Math.max(0, Math.min(10, score));
    
    console.log(`📊 Safety Score Calculated: ${finalScore.toFixed(1)}/10`);
    setSafetyScore(finalScore.toFixed(1));
  };

  const fetchNearbyPlaces = async () => {
    console.log('🔍 fetchNearbyPlaces called');
    console.log('📍 Current location:', currentLocation);
    
    if (!currentLocation || !currentLocation.latitude || !currentLocation.longitude) {
      console.warn('⚠️ Location not available yet, will retry when location is available');
      // Don't set empty array, keep loading state
      return;
    }
    
    // Check cache - only fetch if more than 5 minutes have passed
    const now = Date.now();
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
    
    if (lastPlacesFetchRef.current && 
        (now - lastPlacesFetchRef.current < CACHE_DURATION) &&
        placesCacheRef.current) {
      console.log('🗺️ Using cached places data (within 5 min window)');
      return; // Use existing state, don't refetch
    }
    
    try {
      console.log('🤖 Calling Gemini AI with location:', currentLocation.latitude, currentLocation.longitude);
      
      // Fetch cultural places from Gemini AI based on current location
      const response = await api.post('/cultural/nearby', {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        radius: 10, // 10 km radius
        language: language
      });

      console.log('✅ Gemini AI response:', response.data);

      if (response.data.success && response.data.places) {
        console.log('📝 Processing', response.data.places.length, 'places from Gemini AI');
        
        // Transform Gemini AI data to match our format
        const transformedPlaces = response.data.places.map((place, index) => ({
          id: index + 1,
          name: place.name,
          type: place.type || 'Cultural Site',
          description: place.about || place.description,
          distance: `${place.distance} km`,
          safety: place.safety_level === 'safe' ? 'High Safety' : 
                  place.safety_level === 'moderate' ? 'Medium Safety' : 'Caution',
          rating: place.rating || 4.5,
          icon: getPlaceIcon(place.type),
          dressCode: place.dress_code || 'Modest clothing recommended',
          openingHours: place.opening_hours || 'Check locally',
          entryFee: place.entry_fee || 'Check at entrance',
          bestTime: place.best_time || 'Morning hours',
          safetyTips: place.safety_tips || 'Stay alert and keep belongings secure',
          culturalInfo: place.about || place.description,
          etiquette: place.etiquette || 'Respect local customs',
          photography: place.photography || 'Allowed',
          languages: place.languages_spoken ? place.languages_spoken.split(',').map(l => l.trim()) : ['Hindi', 'English'],
          emergencyContact: place.emergency_contact || '100',
          latitude: place.latitude,
          longitude: place.longitude
        }));
        
        console.log('✅ Cultural places updated with', transformedPlaces.length, 'places');
        setNearbyPlaces(transformedPlaces);
        placesCacheRef.current = transformedPlaces;
        lastPlacesFetchRef.current = now;
        
        // Store in localStorage for offline mode
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('vikranta_places', JSON.stringify(transformedPlaces));
        }
      } else if (response.data.message) {
        // Rate limited - keep existing data
        console.log('⚠️ Rate limited, keeping existing places data');
      } else {
        console.warn('⚠️ No places in Gemini response');
      }
    } catch (error) {
      console.error('❌ Error fetching cultural places from Gemini AI:', error);
      console.error('Error details:', error.response?.data || error.message);
      // Keep existing data on error (don't reset)
    }
  };

  // Helper function to get appropriate icon based on place type
  const getPlaceIcon = (type) => {
    const typeStr = (type || '').toLowerCase();
    if (typeStr.includes('temple')) return '🕉️';
    if (typeStr.includes('fort')) return '🏯';
    if (typeStr.includes('palace')) return '🏰';
    if (typeStr.includes('museum')) return '🏛️';
    if (typeStr.includes('monument')) return '🗿';
    if (typeStr.includes('market')) return '🛍️';
    if (typeStr.includes('garden')) return '🌳';
    return '📍';
  };

  const fetchSafetyZones = async () => {
    try {
      // Fetch real geofences from backend
      const response = await api.get('/geofence/list?active=true');
      const { geofences } = response.data;
      
      if (geofences && geofences.length > 0) {
        // Helper function to calculate distance between two points (Haversine formula)
        const calculateDistance = (lat1, lon1, lat2, lon2) => {
          const R = 6371; // Radius of the Earth in km
          const dLat = (lat2 - lat1) * Math.PI / 180;
          const dLon = (lon2 - lon1) * Math.PI / 180;
          const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon/2) * Math.sin(dLon/2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
          return R * c; // Distance in km
        };

        // Convert geofences to safety zones and calculate distance
        const zones = geofences.map(gf => {
          // Calculate center of polygon
          const coords = gf.polygon?.coordinates?.[0] || [];
          let centerLat = 0, centerLng = 0;
          
          if (coords.length > 0) {
            coords.forEach(coord => {
              const [lng, lat] = typeof coord === 'string' ? coord.split(' ').map(Number) : coord;
              centerLat += lat;
              centerLng += lng;
            });
            centerLat /= coords.length;
            centerLng /= coords.length;
          }

          // Calculate distance from user location
          const distance = currentLocation 
            ? calculateDistance(currentLocation.latitude, currentLocation.longitude, centerLat, centerLng)
            : 999; // Large number if no user location

          return {
            id: gf.id,
            name: gf.name,
            type: gf.zone_type || 'Safety Zone',
            safety: gf.risk_level === 'high' ? 'High Risk' : 
                   gf.risk_level === 'medium' ? 'Medium Safety' : 'High Safety',
            lat: centerLat,
            lng: centerLng,
            distance: distance,
            description: gf.description
          };
        });

        // Filter zones within 50km and sort by distance
        const nearbyZones = zones
          .filter(zone => zone.distance < 50)
          .sort((a, b) => a.distance - b.distance)
          .slice(0, 10); // Show max 10 zones

        console.log(`📍 Found ${nearbyZones.length} zones within 50km`);
        setSafetyZones(nearbyZones);
        setGeofences(geofences); // Store raw geofence data for map rendering
        
        if (nearbyZones.length === 0 && currentLocation) {
          console.log('🤖 No zones nearby, generating new zones with AI...');
          await generateSafetyZones();
        } else if (nearbyZones.length === 0) {
          console.log('⚠️ No zones nearby, showing all zones');
          setSafetyZones(zones.slice(0, 5)); // Show first 5 if none nearby
        }
      } else {
        console.log('⚠️ No geofences from backend, using mock data');
        useMockSafetyZones();
      }
    } catch (error) {
      console.error('Error fetching safety zones:', error);
      useMockSafetyZones();
    }
  };

  const generateSafetyZones = async () => {
    if (!currentLocation) {
      console.log('⚠️ No location available for zone generation');
      return;
    }

    // Check cache - only generate zones if more than 10 minutes have passed
    const now = Date.now();
    const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes
    
    if (lastZonesGenerateRef.current && (now - lastZonesGenerateRef.current < CACHE_DURATION)) {
      console.log('🗺️ Zone generation recently attempted (within 10 min), skipping to avoid rate limit');
      return;
    }

    try {
      console.log('🤖 Generating safety zones for:', currentLocation);
      const response = await api.post('/geofence/generate-nearby', {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        radius: 20
      });

      if (response.data.success) {
        console.log(`✅ Generated ${response.data.zones.length} new zones:`, response.data.zones);
        lastZonesGenerateRef.current = now; // Update cache timestamp
        // Refresh the safety zones list
        await fetchSafetyZones();
      } else if (response.data.message) {
        console.log('⚠️ Zone generation rate limited, will retry later');
        lastZonesGenerateRef.current = now; // Still update timestamp to prevent spam
      }
    } catch (error) {
      console.error('❌ Error generating safety zones:', error);
      lastZonesGenerateRef.current = now; // Update timestamp even on error to prevent spam
    }
  };
  
  const useMockSafetyZones = () => {
    const mockZones = [
      { id: 1, name: 'Hawa Mahal', type: 'Heritage Site', safety: 'High Safety', lat: 26.9239, lng: 75.8267 },
      { id: 2, name: 'City Palace', type: 'Tourist Area', safety: 'Medium Safety', lat: 26.9258, lng: 75.8237 },
      { id: 3, name: 'Amber Fort', type: 'Heritage Site', safety: 'High Safety', lat: 26.9855, lng: 75.8513 }
    ];
    setSafetyZones(mockZones);
  };
  
  const showCulturalDetails = (place) => {
    setCulturalDetails(place);
  };
  
  const closeCulturalDetails = () => {
    setCulturalDetails(null);
  };
  
  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'hi' : 'en');
  };

  const fetchWeather = async () => {
    if (!currentLocation) return;

    try {
      console.log('🌤️ Fetching weather for:', currentLocation);
      const response = await api.get(`/weather/current`, {
        params: {
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude
        }
      });

      if (response.data.success) {
        const data = response.data.weather;
        setWeather({
          temp: Math.round(data.temperature),
          description: data.description,
          icon: data.icon || '🌤️'
        });
        console.log('✅ Weather updated:', data);
      }
    } catch (error) {
      console.error('❌ Error fetching weather:', error);
      // Keep the loading/default state
    }
  };

  const fetchCulturalEvent = async () => {
    if (!currentLocation) return;

    // Check cache - only fetch if more than 5 minutes have passed
    const now = Date.now();
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
    
    if (lastCulturalFetchRef.current && 
        (now - lastCulturalFetchRef.current < CACHE_DURATION) &&
        culturalCacheRef.current) {
      console.log('🎭 Using cached cultural data (within 5 min window)');
      return; // Use existing state, don't refetch
    }

    try {
      console.log('🎭 Fetching cultural events for:', currentLocation);
      const response = await api.get(`/cultural/events`, {
        params: {
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude
        }
      });

      // Backend returns 'places' array OR 'event' object
      if (response.data.success) {
        if (response.data.places && response.data.places.length > 0) {
          // Use first place as the cultural event
          const firstPlace = response.data.places[0];
          const eventData = {
            name: firstPlace.name || 'Cultural Place',
            date: firstPlace.description || 'Nearby attraction'
          };
          setCulturalEvent(eventData);
          culturalCacheRef.current = eventData;
          lastCulturalFetchRef.current = now;
          console.log('✅ Cultural event updated:', eventData);
        } else if (response.data.event) {
          // Fallback to old format
          setCulturalEvent(response.data.event);
          culturalCacheRef.current = response.data.event;
          lastCulturalFetchRef.current = now;
          console.log('✅ Cultural event updated:', response.data.event);
        } else if (response.data.message) {
          // Rate limited - keep existing data
          console.log('⚠️ Rate limited, keeping existing data');
        }
      }
    } catch (error) {
      console.error('❌ Error fetching cultural event:', error);
      // Keep the existing state on error (don't reset to loading)
    }
  };

  const handleSOSClick = async () => {
    if (emergencyActive) return;
    
    // Check if location is available
    if (!currentLocation?.latitude || !currentLocation?.longitude) {
      alert('⚠️ Location not available!\n\nPlease wait for GPS signal before using SOS.');
      return;
    }
    
    setEmergencyActive(true);
    
    try {
      const response = await api.post('/incident/panic', {
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        address: currentLocation.address || 'Location detected',
        description: '🚨 EMERGENCY SOS ACTIVATED by tourist'
      });
      
      console.log('✅ SOS sent successfully:', response.data);
      
      toast.success('🚨 EMERGENCY SOS ACTIVATED!\n\n✅ All authorities have been notified\n📍 Your location shared\n\nHelp is on the way!', {
        autoClose: 8000,
        position: 'top-center',
        style: {
          backgroundColor: '#ff4444',
          color: 'white',
          fontSize: '16px',
          fontWeight: 'bold'
        }
      });
      
      // Keep emergency active for 5 minutes
      setTimeout(() => setEmergencyActive(false), 300000);
    } catch (error) {
      console.error('❌ SOS Error:', error);
      toast.error('Failed to send SOS. Please try again or call emergency services directly.', {
        autoClose: 5000
      });
      setEmergencyActive(false);
    }
  };

  const handleEndJourney = () => {
    setShowEndJourneyModal(true);
  };

  const confirmEndJourney = async () => {
    try {
      // Delete tourist account and all data from database
      await api.delete('/user/account');
      
      console.log('✅ Journey ended. Tourist account deleted from database.');
      
      // Show farewell message
      alert('🎉 Journey Complete!\n\nThank you for using VIKRANTA!\n\nYour account and data have been securely removed.\n\nSafe travels! 🌍');
      
      // Logout and redirect to login
      logout();
    } catch (error) {
      console.error('Error ending journey:', error);
      alert('⚠️ Error ending journey. Please try again or contact support.');
      setShowEndJourneyModal(false);
    }
  };

  const cancelEndJourney = () => {
    setShowEndJourneyModal(false);
  };

  const closeProfileSidebar = () => {
    setShowProfileSidebar(false);
  };

  const getDirections = (place) => {
    // Use actual coordinates if available (from Gemini AI data)
    if (place.latitude && place.longitude) {
      const url = `https://www.google.com/maps/dir/?api=1&origin=${currentLocation.latitude},${currentLocation.longitude}&destination=${place.latitude},${place.longitude}&travelmode=driving`;
      window.open(url, '_blank');
    } else {
      // Fallback to place name search
      const destination = encodeURIComponent(place.name);
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${destination}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Status Notification Banner */}
      {showStatusNotification && incidentStatus && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-md px-4">
          <div className={`rounded-lg shadow-2xl p-4 animate-bounce ${
            incidentStatus.status === 'acknowledged' ? 'bg-yellow-50 border-2 border-yellow-400' :
            incidentStatus.status === 'en_route' ? 'bg-blue-50 border-2 border-blue-400' :
            'bg-green-50 border-2 border-green-400'
          }`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <span className="text-3xl">
                  {incidentStatus.status === 'acknowledged' ? '👀' :
                   incidentStatus.status === 'en_route' ? '🚓' : '✅'}
                </span>
                <div>
                  <p className="font-bold text-lg">
                    {incidentStatus.status === 'acknowledged' ? 'Help Acknowledged' :
                     incidentStatus.status === 'en_route' ? 'Help is On The Way!' :
                     'Incident Resolved'}
                  </p>
                  <p className="text-sm text-gray-700 mt-1">{incidentStatus.message}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    From: {incidentStatus.authority_name} • {new Date(incidentStatus.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowStatusNotification(false)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white shadow-md px-4 py-3 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <img 
            src="/logo.jpg" 
            alt="VIKRANTA Logo" 
            className="h-10 object-contain"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="40">🛡️</text></svg>';
            }}
          />
          <h1 className="text-2xl font-bold text-teal-600">VIKRANTA</h1>
          
          {isOfflineMode && (
            <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full flex items-center space-x-1">
              <span>📵</span>
              <span>{t('offlineMode')}</span>
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleLanguage}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold transition-all"
            title="Change Language"
          >
            {language === 'en' ? '🇮🇳 हिन्दी' : '🇬🇧 English'}
          </button>
          
          <button 
            onClick={() => setShowProfileSidebar(true)}
            className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center hover:bg-teal-700 transition-all shadow-md"
          >
            <span className="text-white text-xl">👤</span>
          </button>
        </div>
      </div>
      
      {/* Geofence Alerts */}
      {geofenceAlerts.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
          {geofenceAlerts.map(alert => (
            <div key={alert.id} className="flex items-center space-x-2">
              <span className="text-yellow-700 font-semibold">{alert.message}</span>
            </div>
          ))}
        </div>
      )}

      {showProfileSidebar && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={closeProfileSidebar}
          ></div>
          
          <div className="fixed right-0 top-0 h-full w-80 bg-gray-900 shadow-2xl z-50 overflow-y-auto">
            <div className="p-6">
              <button 
                onClick={closeProfileSidebar}
                className="absolute top-4 right-4 text-white text-2xl hover:text-gray-300"
              >
                
              </button>

              <div className="mb-6 pb-6 border-b border-gray-700">
                <h3 className="text-white text-lg font-bold mb-4"> Profile Details</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-gray-400 text-xs">Name</p>
                    <p className="text-white">{user?.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Email</p>
                    <p className="text-white text-sm">{user?.email}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Phone</p>
                    <p className="text-white">{user?.phone || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Emergency Contact</p>
                    <p className="text-white">{user?.emergency_contact || 'Not provided'}</p>
                  </div>
                </div>
              </div>

              <div className="mb-6 pb-6 border-b border-gray-700">
                <h3 className="text-white text-lg font-bold mb-4"> Emergency Services</h3>
                <div className="space-y-3">
                  <a href="tel:100" className="block w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg flex items-center justify-center space-x-2 transition-all">
                    <span></span>
                    <span>Police: 100</span>
                  </a>
                  <a href="tel:108" className="block w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg flex items-center justify-center space-x-2 transition-all">
                    <span></span>
                    <span>Medical: 108</span>
                  </a>
                  {user?.emergency_contact && (
                    <a href={`tel:${user.emergency_contact}`} className="block w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg flex items-center justify-center space-x-2 transition-all">
                      <span></span>
                      <span>My Emergency: {user.emergency_contact.substring(0, 10)}</span>
                    </a>
                  )}
                  <a href="tel:1363" className="block w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg flex items-center justify-center space-x-2 transition-all">
                    <span></span>
                    <span>Tourist Helpline: 1363</span>
                  </a>
                </div>
              </div>

              <div className="mb-6 pb-6 border-b border-gray-700">
                <h3 className="text-white text-lg font-bold mb-4">🔔 Active Alerts</h3>
                <div className="space-y-3">
                  <div className="bg-blue-900 bg-opacity-50 p-3 rounded-lg">
                    <p className="text-blue-300 text-sm font-semibold flex items-center">
                      <span className="mr-2">{weather.icon}</span> Weather
                    </p>
                    <p className="text-gray-300 text-xs mt-1">
                      {weather.description}, {weather.temp}°C
                    </p>
                  </div>
                  <div className="bg-purple-900 bg-opacity-50 p-3 rounded-lg">
                    <p className="text-purple-300 text-sm font-semibold flex items-center">
                      <span className="mr-2">🎭</span> Cultural Event
                    </p>
                    <p className="text-gray-300 text-xs mt-1">
                      {culturalEvent.name} {culturalEvent.date && `- ${culturalEvent.date}`}
                    </p>
                  </div>
                  <div className="bg-green-900 bg-opacity-50 p-3 rounded-lg">
                    <p className="text-green-300 text-sm font-semibold flex items-center">
                      <span className="mr-2">🛡️</span> Safety Status
                    </p>
                    <p className="text-gray-300 text-xs mt-1">Area is safe - Score: {safetyScore}/10</p>
                  </div>
                </div>
              </div>

              <button 
                onClick={logout}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg transition-all font-semibold"
              >
                🚪 Logout
              </button>

              <button 
                onClick={handleEndJourney}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white py-3 rounded-lg transition-all font-semibold mt-3 flex items-center justify-center space-x-2"
              >
                <span>🏁</span>
                <span>End Journey</span>
              </button>
            </div>
          </div>
        </>
      )}

      <div className="pb-20">
        {activeView === 'dashboard' && (
          <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
            <div className="text-center w-full flex flex-col items-center">
              <button
                onClick={handleSOSClick}
                disabled={emergencyActive}
                className={`w-64 h-64 rounded-full flex flex-col items-center justify-center text-white font-bold text-2xl shadow-2xl transition-all transform mx-auto ${
                  emergencyActive 
                    ? 'bg-red-800 animate-pulse cursor-not-allowed' 
                    : 'bg-red-600 hover:bg-red-700 hover:scale-105 active:scale-95'
                }`}
              >
                <span className="text-6xl mb-4">🚨</span>
                <span className="text-3xl">SOS</span>
                <span className="text-lg mt-2">{emergencyActive ? 'ACTIVE' : 'Emergency'}</span>
              </button>
              
              {emergencyActive && (
                <div className="mt-8 bg-red-100 border-2 border-red-600 rounded-lg p-4 max-w-md mx-auto">
                  <p className="text-red-800 font-bold text-lg"> EMERGENCY ACTIVE</p>
                  <p className="text-red-700 text-sm mt-2">Authorities have been notified of your location</p>
                </div>
              )}
              
              {!emergencyActive && (
                <p className="mt-6 text-gray-600 max-w-md mx-auto">
                  Press the SOS button in case of emergency.<br/>
                  Your location and details will be immediately sent to authorities.
                </p>
              )}

              <div className="mt-12 grid grid-cols-3 gap-4 max-w-2xl mx-auto">
                <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
                  <div className="text-3xl mb-2">🛡️</div>
                  <div className="text-2xl font-bold text-teal-700">{safetyScore}</div>
                  <div className="text-xs text-gray-600">Safety Score</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-3xl mb-2">📍</div>
                  <div className="text-sm font-bold text-blue-700">Tracked</div>
                  <div className="text-xs text-gray-600">Location Active</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-3xl mb-2">✓</div>
                  <div className="text-sm font-bold text-green-700">Verified</div>
                  <div className="text-xs text-gray-600">Profile</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'map' && (
          <div className="h-[calc(100vh-140px)]">
            <div className="h-full relative">
              {currentLocation?.latitude && currentLocation?.longitude ? (
                <>
                <Map
                  initialViewState={{
                    longitude: currentLocation.longitude,
                    latitude: currentLocation.latitude,
                    zoom: 12
                  }}
                  style={{width: '100%', height: '100%'}}
                  mapStyle="mapbox://styles/mapbox/streets-v12"
                  mapboxAccessToken={MAPBOX_TOKEN}
                >
                {/* Render geofence polygons */}
                {geofences.map(geofence => {
                  // Convert polygon coordinates to GeoJSON format
                  const coords = geofence.polygon?.coordinates?.[0] || [];
                  const geoJsonCoords = coords.map(coord => {
                    if (typeof coord === 'string') {
                      const [lng, lat] = coord.split(' ').map(Number);
                      return [lng, lat];
                    }
                    return coord;
                  });

                  // Determine color based on risk level
                  const fillColor = geofence.risk_level === 'low' ? '#10b981' :  // green
                                   geofence.risk_level === 'medium' ? '#f59e0b' : // yellow
                                   '#ef4444'; // red
                  
                  const fillOpacity = 0.15;
                  const borderColor = geofence.risk_level === 'low' ? '#059669' :
                                     geofence.risk_level === 'medium' ? '#d97706' :
                                     '#dc2626';

                  return (
                    <Source
                      key={`geofence-${geofence.id}`}
                      type="geojson"
                      data={{
                        type: 'Feature',
                        geometry: {
                          type: 'Polygon',
                          coordinates: [geoJsonCoords]
                        },
                        properties: {
                          name: geofence.name,
                          risk_level: geofence.risk_level
                        }
                      }}
                    >
                      <Layer
                        id={`geofence-fill-${geofence.id}`}
                        type="fill"
                        paint={{
                          'fill-color': fillColor,
                          'fill-opacity': fillOpacity
                        }}
                      />
                      <Layer
                        id={`geofence-outline-${geofence.id}`}
                        type="line"
                        paint={{
                          'line-color': borderColor,
                          'line-width': 2
                        }}
                      />
                    </Source>
                  );
                })}

                {currentLocation && (
                  <>
                    {/* Accuracy circle */}
                    <Marker
                      longitude={currentLocation.longitude}
                      latitude={currentLocation.latitude}
                      anchor="center"
                    >
                      <div 
                        className="rounded-full bg-blue-200 opacity-30 border-2 border-blue-400"
                        style={{
                          width: `${Math.min(currentLocation.accuracy / 2, 100)}px`,
                          height: `${Math.min(currentLocation.accuracy / 2, 100)}px`,
                        }}
                      />
                    </Marker>
                    
                    {/* User location marker */}
                    <Marker
                      longitude={currentLocation.longitude}
                      latitude={currentLocation.latitude}
                      anchor="bottom"
                    >
                      <div className="relative">
                        <div className="w-6 h-6 bg-blue-600 rounded-full border-4 border-white shadow-lg animate-pulse"></div>
                        <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 text-xs bg-blue-600 text-white px-2 py-1 rounded whitespace-nowrap shadow-lg">
                          You are here
                          <div className="text-[10px] opacity-80">
                            ±{Math.round(currentLocation.accuracy)}m
                          </div>
                        </div>
                      </div>
                    </Marker>
                  </>
                )}

                {safetyZones.map(zone => (
                  <Marker
                    key={zone.id}
                    longitude={zone.lng}
                    latitude={zone.lat}
                    anchor="bottom"
                  >
                    <div className="text-2xl cursor-pointer hover:scale-110 transition-transform">
                      {zone.safety === 'High Safety' ? '🟢' : zone.safety === 'Medium Safety' ? '🟡' : '🔴'}
                    </div>
                  </Marker>
                ))}
              </Map>
              
              <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-xs">
                  <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                    <span className="text-xl mr-2">🗺️</span>
                    Safety Map
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">🟢</span>
                      <span className="text-gray-700">Safe Zone</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-yellow-600">🟡</span>
                      <span className="text-gray-700">Caution Zone</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-red-600">🔴</span>
                      <span className="text-gray-700">High Risk Zone</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-blue-600">📍</span>
                      <span className="text-gray-700">Your Location</span>
                    </div>
                  </div>
                </div>

                <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg p-4 max-h-48 overflow-y-auto">
                  <h3 className="font-bold text-gray-800 mb-3">Nearby Safety Zones</h3>
                  <div className="space-y-2">
                    {safetyZones.map(zone => (
                      <div key={zone.id} className="flex justify-between items-center border-b border-gray-200 pb-2">
                        <div>
                          <p className="font-semibold text-gray-800 text-sm">{zone.name}</p>
                          <p className="text-xs text-gray-600">{zone.type}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          zone.safety === 'High Safety' ? 'bg-green-100 text-green-700' :
                          zone.safety === 'Medium Safety' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {zone.safety}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-full bg-gray-50">
                  <div className="text-center p-8">
                    <div className="text-6xl mb-4">📍</div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">Getting your location...</h3>
                    <p className="text-gray-600 mb-4">Please allow location access when prompted</p>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vikranta-saffron mx-auto"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeView === 'cultural' && (
          <div className="p-4 max-w-4xl mx-auto">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-800 flex items-center">
                <span className="text-3xl mr-3">🏛️</span>
                Cultural Guide
              </h1>
              <p className="text-gray-600 mt-2">Discover nearby places to visit</p>
            </div>

            <div className="space-y-4">
              {nearbyPlaces.length === 0 ? (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-8 text-center">
                  <div className="animate-pulse">
                    <div className="text-6xl mb-4">🤖</div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">
                      VIKRANTA is finding cultural places...
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Analyzing your location and discovering the best cultural attractions nearby
                    </p>
                    <div className="flex justify-center items-center space-x-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                      <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-3 h-3 bg-pink-500 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
                    </div>
                  </div>
                </div>
              ) : (
                nearbyPlaces.map(place => (
                <div key={place.id} className="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-xl p-5 shadow-md hover:shadow-lg transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-4xl">{place.icon}</span>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800">{place.name}</h3>
                          <p className="text-sm text-gray-600">{place.type}</p>
                        </div>
                      </div>
                      
                      <p className="text-gray-700 mb-3 text-sm">{place.description}</p>
                      
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="flex items-center text-gray-600">
                          <span className="mr-1">📏</span>
                          {place.distance}
                        </span>
                        <span className="flex items-center text-yellow-600">
                          <span className="mr-1">⭐</span>
                          {place.rating}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          place.safety === 'High Safety' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {place.safety}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 flex space-x-3">
                    <button
                      onClick={() => getDirections(place)}
                      className="flex-1 bg-teal-600 hover:bg-teal-700 text-white py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all"
                    >
                      <span>🧭</span>
                      <span className="font-semibold">{t('getDirections')}</span>
                    </button>
                    <button 
                      onClick={() => showCulturalDetails(place)}
                      className="bg-white border-2 border-teal-600 text-teal-600 hover:bg-teal-50 py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all"
                    >
                      <span>ℹ️</span>
                      <span className="font-semibold">{t('details')}</span>
                    </button>
                  </div>
                  
                  {place.openingHours && (
                    <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-blue-800 text-xs font-semibold flex items-center">
                        <span className="mr-2">🕐</span>
                        Hours: {place.openingHours}
                      </p>
                    </div>
                  )}

                  {place.dressCode && (
                    <div className="mt-3 bg-cyan-100 border border-cyan-300 rounded-lg p-3">
                      <p className="text-cyan-800 text-xs font-semibold flex items-center">
                        <span className="mr-2">💡</span>
                        Dress Code: {place.dressCode}
                      </p>
                    </div>
                  )}
                  {place.etiquette && (
                    <div className="mt-3 bg-blue-100 border border-blue-300 rounded-lg p-3">
                      <p className="text-blue-800 text-xs font-semibold flex items-center">
                        <span className="mr-2">🎫</span>
                        Etiquette: {place.etiquette}
                      </p>
                    </div>
                  )}
                  {place.tip && (
                    <div className="mt-3 bg-purple-100 border border-purple-300 rounded-lg p-3">
                      <p className="text-purple-800 text-xs font-semibold flex items-center">
                        <span className="mr-2">⚠️</span>
                        Safety: {place.tip}
                      </p>
                    </div>
                  )}
                </div>
              )))}
            </div>
          </div>
        )}
      </div>
      
      {/* Cultural Details Modal */}
      {culturalDetails && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={closeCulturalDetails}
          ></div>
          
          <div className="fixed inset-x-4 top-20 bottom-20 md:inset-x-auto md:left-1/2 md:transform md:-translate-x-1/2 md:w-full md:max-w-2xl bg-white rounded-xl shadow-2xl z-50 overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-teal-600 to-blue-600 text-white p-4 flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <span className="text-4xl">{culturalDetails.icon}</span>
                <div>
                  <h2 className="text-xl font-bold">{culturalDetails.name}</h2>
                  <p className="text-sm opacity-90">{culturalDetails.type}</p>
                </div>
              </div>
              <button 
                onClick={closeCulturalDetails}
                className="text-white text-2xl hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-bold text-gray-800 mb-2 flex items-center">
                  <span className="text-xl mr-2">📖</span>
                  About
                </h3>
                <p className="text-gray-700 text-sm">{culturalDetails.description}</p>
                <p className="text-gray-600 text-sm mt-2 italic">{culturalDetails.culturalInfo}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-blue-800 text-xs font-semibold mb-1">🕐 Opening Hours</p>
                  <p className="text-blue-900 text-sm">{culturalDetails.openingHours}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-green-800 text-xs font-semibold mb-1">💰 Entry Fee</p>
                  <p className="text-green-900 text-sm">{culturalDetails.entryFee}</p>
                </div>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-bold text-yellow-800 mb-2 flex items-center">
                  <span className="text-xl mr-2">⏰</span>
                  Best Time to Visit
                </h3>
                <p className="text-yellow-900 text-sm">{culturalDetails.bestTime}</p>
              </div>
              
              {culturalDetails.dressCode && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h3 className="font-bold text-purple-800 mb-2 flex items-center">
                    <span className="text-xl mr-2">👔</span>
                    Dress Code
                  </h3>
                  <p className="text-purple-900 text-sm">{culturalDetails.dressCode}</p>
                </div>
              )}
              
              {culturalDetails.etiquette && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-bold text-blue-800 mb-2 flex items-center">
                    <span className="text-xl mr-2">🙏</span>
                    Etiquette
                  </h3>
                  <p className="text-blue-900 text-sm">{culturalDetails.etiquette}</p>
                </div>
              )}
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="font-bold text-red-800 mb-2 flex items-center">
                  <span className="text-xl mr-2">⚠️</span>
                  Safety Tips
                </h3>
                <p className="text-red-900 text-sm">{culturalDetails.safetyTips || culturalDetails.tip}</p>
              </div>
              
              <div className="bg-gray-100 rounded-lg p-4">
                <h3 className="font-bold text-gray-800 mb-2 flex items-center">
                  <span className="text-xl mr-2">🗣️</span>
                  Languages Available
                </h3>
                <div className="flex flex-wrap gap-2">
                  {culturalDetails.languages?.map(lang => (
                    <span key={lang} className="bg-white px-3 py-1 rounded-full text-sm text-gray-700 border">
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
              
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <h3 className="font-bold text-orange-800 mb-2 flex items-center">
                  <span className="text-xl mr-2">📞</span>
                  Emergency Contact
                </h3>
                <a href={`tel:${culturalDetails.emergencyContact}`} className="text-orange-900 text-lg font-mono hover:underline">
                  {culturalDetails.emergencyContact}
                </a>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => getDirections(culturalDetails)}
                  className="flex-1 bg-teal-600 hover:bg-teal-700 text-white py-3 px-4 rounded-lg font-semibold transition-all flex items-center justify-center space-x-2"
                >
                  <span>🧭</span>
                  <span>Get Directions</span>
                </button>
                <button
                  onClick={closeCulturalDetails}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-3 px-6 rounded-lg font-semibold transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 px-4 py-3 shadow-lg">
        <div className="flex justify-around items-center max-w-md mx-auto">
          <button 
            onClick={() => setActiveView('dashboard')}
            className={`flex flex-col items-center space-y-1 transition-all ${
              activeView === 'dashboard' ? 'text-teal-600' : 'text-gray-400'
            }`}
          >
            <span className="text-3xl">🏠</span>
            <span className="text-xs font-semibold">{t('dashboard')}</span>
          </button>
          
          <button 
            onClick={() => setActiveView('map')}
            className={`flex flex-col items-center space-y-1 transition-all ${
              activeView === 'map' ? 'text-teal-600' : 'text-gray-400'
            }`}
          >
            <span className="text-3xl">🗺️</span>
            <span className="text-xs font-semibold">{t('map')}</span>
          </button>
          
          <button 
            onClick={() => setActiveView('cultural')}
            className={`flex flex-col items-center space-y-1 transition-all ${
              activeView === 'cultural' ? 'text-teal-600' : 'text-gray-400'
            }`}
          >
            <span className="text-3xl">🏛️</span>
            <span className="text-xs font-semibold">{t('cultural')}</span>
          </button>
        </div>
      </div>

      {/* End Journey Confirmation Modal */}
      {showEndJourneyModal && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={cancelEndJourney}
          ></div>
          
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl z-50 p-6 max-w-md w-full mx-4">
            <div className="text-center">
              <div className="text-6xl mb-4">🏁</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">End Your Journey?</h2>
              <p className="text-gray-600 mb-4">
                Ending your journey will permanently delete your account and all data from our system.
              </p>
              
              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-800 font-bold text-sm mb-2">⚠️ Warning</p>
                <p className="text-red-700 text-xs">
                  • Your account will be deleted<br/>
                  • All journey data will be removed<br/>
                  • This action cannot be undone
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={cancelEndJourney}
                  className="flex-1 px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-semibold transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmEndJourney}
                  className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all"
                >
                  End Journey
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
