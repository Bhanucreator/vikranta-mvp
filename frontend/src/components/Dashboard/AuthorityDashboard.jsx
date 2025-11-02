import React, { useEffect, useState, useRef } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import api from '../../services/api'
import { toast } from 'react-toastify'
import { io } from 'socket.io-client'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

const BACKEND_URL = 'http://localhost:5000'
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

mapboxgl.accessToken = MAPBOX_TOKEN

export default function AuthorityDashboard() {
  const { user } = useAuth() 
  const [incidents, setIncidents] = useState([])
  const [tourists, setTourists] = useState([])
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [showChat, setShowChat] = useState(false)
  const [chatMessages, setChatMessages] = useState([])
  const [messageInput, setMessageInput] = useState('')
  const [showAddAuthority, setShowAddAuthority] = useState(false)
  const [newAuthority, setNewAuthority] = useState({
    name: '',
    email: '',
    phone: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('map') // 'map' or 'list'
  const [showResolved, setShowResolved] = useState(false) // Filter for resolved incidents
  
  const socketRef = useRef(null)
  const mapRef = useRef(null)
  const mapContainerRef = useRef(null)
  const markersRef = useRef({})

  useEffect(() => {
    fetchIncidents()
    fetchTouristLocations()
    initializeWebSocket()
    
    // Refresh tourist locations every 10 seconds
    const locationInterval = setInterval(fetchTouristLocations, 10000)
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
      if (mapRef.current) {
        try {
          mapRef.current.remove()
          mapRef.current = null
        } catch (error) {
          console.log('Map cleanup error (non-critical):', error)
        }
      }
      clearInterval(locationInterval)
    }
  }, [])

  // Initialize map only when in map view
  useEffect(() => {
    if (viewMode === 'map' && mapContainerRef.current && !mapRef.current) {
      initializeMap()
    }
  }, [viewMode])

  const initializeMap = () => {
    if (!mapContainerRef.current) return
    if (mapRef.current) return // Already initialized

    try {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [77.5946, 12.9716], // Bangalore
        zoom: 11
      })

      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right')
      mapRef.current.addControl(new mapboxgl.FullscreenControl(), 'top-right')

      // Wait for map to load before adding markers
      mapRef.current.on('load', () => {
        console.log('🗺️ Map initialized and ready')
        // Update markers after map is ready
        if (incidents.length > 0 || tourists.length > 0) {
          updateMapMarkers()
        }
      })
    } catch (error) {
      console.error('Error initializing map:', error)
    }
  }

  const updateMapMarkers = () => {
    // Only update markers if map exists and is in map view
    if (!mapRef.current || viewMode !== 'map') return
    
    // Check if map is loaded
    if (!mapRef.current.loaded()) {
      console.log('⏳ Map not loaded yet, waiting...')
      return
    }

    try {
      // Clear existing markers
      Object.values(markersRef.current).forEach(marker => {
        try {
          marker.remove()
        } catch (e) {
          console.log('Marker removal error (non-critical):', e)
        }
      })
      markersRef.current = {}

      // Track if we have any critical incidents to auto-open
      let firstCriticalIncident = null

      // Add incident markers (RED with BLINKING for critical) - EXCLUDE RESOLVED INCIDENTS
      incidents.filter(incident => incident.status !== 'resolved').forEach(incident => {
        if (incident.location && incident.location.latitude && incident.location.longitude) {
          const el = document.createElement('div')
          el.className = 'incident-marker'
          el.style.width = '40px'
          el.style.height = '40px'
          el.style.cursor = 'pointer'
          
          // Add blinking animation for critical active incidents
          const isBlinking = incident.status === 'active' && incident.priority === 'critical'
        
        el.innerHTML = `
          <style>
            @keyframes blink-red {
              0%, 50% { opacity: 1; transform: scale(1); }
              25% { opacity: 0.4; transform: scale(1.2); }
              75% { opacity: 0.7; transform: scale(0.9); }
            }
          </style>
          <div style="
            background: ${incident.status === 'active' ? '#ff0000' : 
                        incident.status === 'acknowledged' ? '#ffa500' :
                        incident.status === 'en_route' ? '#0066ff' : '#00ff00'};
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 ${isBlinking ? '20px' : '10px'} rgba(255,0,0,${isBlinking ? '0.8' : '0.5'});
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            animation: ${isBlinking ? 'blink-red 1.5s infinite' : 'none'};
          ">🚨</div>
        `

        const popup = new mapboxgl.Popup({ 
          closeButton: true,
          closeOnClick: false,
          maxWidth: '300px'
        }).setHTML(`
          <div style="padding: 12px;">
            <h3 style="font-weight: bold; margin-bottom: 8px; color: #ff0000;">
              🚨 ${incident.type.toUpperCase()}
            </h3>
            <div style="background: ${
              incident.priority === 'critical' ? '#ff0000' :
              incident.priority === 'high' ? '#ffa500' : '#ffcc00'
            }; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; font-size: 11px; font-weight: bold;">
              ${incident.priority.toUpperCase()} PRIORITY
            </div>
            <p style="margin: 6px 0;"><strong>Status:</strong> 
              <span style="padding: 2px 6px; border-radius: 3px; background: ${
                incident.status === 'active' ? '#ff0000' :
                incident.status === 'acknowledged' ? '#ffa500' :
                incident.status === 'en_route' ? '#0066ff' : '#00ff00'
              }; color: white; font-size: 11px;">${incident.status.toUpperCase()}</span>
            </p>
            <p style="margin: 6px 0;"><strong>Tourist:</strong> ${incident.user_name || 'Unknown'}</p>
            <p style="margin: 6px 0;"><strong>📞 Phone:</strong> <a href="tel:${incident.user_phone}" style="color: #0066ff;">${incident.user_phone || 'N/A'}</a></p>
            <p style="margin: 6px 0;"><strong>📧 Email:</strong> ${incident.user_email || 'N/A'}</p>
            <p style="margin: 6px 0;"><strong>📍 Location:</strong> ${incident.address || 'Unknown'}</p>
            <p style="margin: 6px 0; font-size: 12px; color: #666;">${incident.description}</p>
            <p style="margin: 6px 0; font-size: 11px; color: #999;">🕐 ${new Date(incident.created_at).toLocaleString()}</p>
            <button onclick="window.selectIncident(${incident.id})" style="
              margin-top: 10px;
              padding: 8px 16px;
              background: #0066ff;
              color: white;
              border: none;
              border-radius: 6px;
              cursor: pointer;
              font-weight: bold;
              width: 100%;
            ">RESPOND NOW</button>
          </div>
        `)

        const marker = new mapboxgl.Marker(el)
          .setLngLat([incident.location.longitude, incident.location.latitude])
          .setPopup(popup)
          .addTo(mapRef.current)

        markersRef.current[`incident_${incident.id}`] = marker

        // Auto-open popup for first critical active incident
        if (incident.status === 'active' && incident.priority === 'critical' && !firstCriticalIncident) {
          firstCriticalIncident = incident
          setTimeout(() => {
            marker.togglePopup()
            // Fly to this incident
            mapRef.current.flyTo({
              center: [incident.location.longitude, incident.location.latitude],
              zoom: 15,
              duration: 2000
            })
          }, 500)
        }

        el.addEventListener('click', () => {
          setSelectedIncident(incident)
          setViewMode('list')
        })
      }
    })

    // Add tourist markers (GREEN)
    tourists.forEach(tourist => {
      if (tourist.latitude && tourist.longitude) {
        const el = document.createElement('div')
        el.className = 'tourist-marker'
        el.style.width = '30px'
        el.style.height = '30px'
        el.innerHTML = `
          <div style="
            background: #00cc00;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 5px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
          ">👤</div>
        `

        const marker = new mapboxgl.Marker(el)
          .setLngLat([tourist.longitude, tourist.latitude])
          .setPopup(new mapboxgl.Popup().setHTML(`
            <div style="padding: 10px;">
              <h4 style="font-weight: bold; margin-bottom: 6px;">👤 ${tourist.name}</h4>
              <p style="margin: 4px 0; font-size: 12px;"><strong>📞 Phone:</strong> <a href="tel:${tourist.phone}" style="color: #0066ff;">${tourist.phone}</a></p>
              <p style="margin: 4px 0; font-size: 12px;"><strong>📧 Email:</strong> ${tourist.email || 'N/A'}</p>
              <p style="margin: 4px 0; font-size: 11px; color: #666;"><strong>Last seen:</strong> ${tourist.last_location_update}</p>
            </div>
          `))
          .addTo(mapRef.current)

        markersRef.current[`tourist_${tourist.id}`] = marker
      }
    })

      console.log(`🗺️ Map updated: ${incidents.length} incidents, ${tourists.length} tourists`)
      if (firstCriticalIncident) {
        console.log(`🚨 Auto-opened critical incident #${firstCriticalIncident.id}`)
      }
    } catch (error) {
      console.error('Error updating map markers:', error)
    }
  }

  useEffect(() => {
    // Only update markers if in map view and map is loaded
    if (viewMode === 'map' && mapRef.current && mapRef.current.loaded() && (incidents.length > 0 || tourists.length > 0)) {
      updateMapMarkers()
    }
  }, [incidents, tourists, viewMode])

  // Make selectIncident available globally for popup buttons
  useEffect(() => {
    window.selectIncident = (id) => {
      const incident = incidents.find(inc => inc.id === id)
      if (incident) {
        setSelectedIncident(incident)
        setViewMode('list')
      }
    }
  }, [incidents])

  // Auto-join incident chat room when incident is selected
  useEffect(() => {
    if (selectedIncident && socketRef.current) {
      console.log(`💬 Joining incident room for Incident #${selectedIncident.id}`)
      socketRef.current.emit('join_incident_room', { incident_id: selectedIncident.id })
      // Clear previous chat messages and set showChat to false initially
      setChatMessages([])
    }
  }, [selectedIncident])

  const fetchIncidents = async () => {
    try {
      const response = await api.get('/incident/list')
      // Flatten user data for easier access
      const processedIncidents = response.data.incidents.map(incident => ({
        ...incident,
        user_name: incident.user?.name || 'Unknown',
        user_phone: incident.user?.phone || null,
        user_email: incident.user?.email || null
      }))
      setIncidents(processedIncidents)
      console.log('✅ Fetched incidents:', processedIncidents.length)
    } catch (error) {
      console.error('Failed to fetch incidents:', error)
    }
  }

  const fetchTouristLocations = async () => {
    try {
      const response = await api.get('/location/all-tourists')
      setTourists(response.data.locations || [])
      console.log('✅ Fetched tourist locations:', response.data.locations?.length || 0)
    } catch (error) {
      console.error('Failed to fetch tourist locations:', error)
    }
  }

  const initializeWebSocket = () => {
    console.log('🔌 Connecting Authority to WebSocket...')
    
    // Configure Socket.IO with better error handling and transport options
    socketRef.current = io(BACKEND_URL, {
      transports: ['polling', 'websocket'], // Try polling first, then websocket
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000,
    })
    
    socketRef.current.on('connect', () => {
      console.log('✅ Authority connected to WebSocket')
      socketRef.current.emit('join_authority_room')
      console.log('👮 Joined authorities room')
    })
    
    socketRef.current.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error.message);
      console.log('🔄 Will retry connection...');
    });
    
    socketRef.current.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected to WebSocket (attempt ${attemptNumber})`);
      socketRef.current.emit('join_authority_room');
    });
    
    socketRef.current.on('disconnect', () => {
      console.log('❌ Authority disconnected from WebSocket')
    })
    
    socketRef.current.on('joined', (data) => {
      console.log('✅ Joined room:', data.room)
      toast.success('Connected to real-time alert system', { autoClose: 2000 })
    })
    
    socketRef.current.on('new_incident', (data) => {
      console.log('🚨 NEW INCIDENT ALERT:', data)
      
      const newIncident = {
        id: data.incident_id,
        type: data.type,
        priority: data.priority,
        status: data.status,
        description: data.description,
        address: data.address,
        created_at: data.timestamp,
        user_name: data.user.name,
        user_phone: data.user.phone,
        user_email: data.user.email,
        location: data.location
      }
      
      setIncidents(prev => [newIncident, ...prev])
      
      toast.error(`🚨 ${data.priority.toUpperCase()} ALERT: ${data.type} from ${data.user.name}`, {
        autoClose: false,
        position: 'top-center',
        style: {
          backgroundColor: '#ff4444',
          color: 'white',
          fontSize: '16px',
          fontWeight: 'bold'
        }
      })
      
      try {
        const audio = new Audio('/alert.mp3')
        audio.play().catch(e => console.log('Could not play alert sound'))
      } catch (e) {
        console.log('Audio not available')
      }
    })
    
    // Listen for chat messages
    socketRef.current.on('new_message', (data) => {
      console.log('💬 New chat message received:', data)
      
      // Add message to chat if incident is selected
      if (selectedIncident && data.incident_id === selectedIncident.id) {
        setChatMessages(prev => [...prev, data])
      }
      
      // Show notification if message is from tourist
      if (data.sender_role === 'tourist') {
        // Find which incident this message belongs to
        const incident = incidents.find(inc => inc.id === data.incident_id)
        const incidentName = incident ? `Incident #${incident.id}` : 'Tourist'
        
        toast.info(`💬 New message from ${data.sender_name} (${incidentName})`, {
          autoClose: 5000,
          position: 'bottom-right',
          onClick: () => {
            // Open chat when clicked
            const inc = incidents.find(i => i.id === data.incident_id)
            if (inc) {
              setSelectedIncident(inc)
              setShowChat(true)
              setViewMode('list')
            }
          }
        })
        
        // Play notification sound
        try {
          const audio = new Audio('/notification.mp3')
          audio.play().catch(e => console.log('Could not play notification sound'))
        } catch (e) {
          console.log('Audio not available')
        }
      }
    })
    
    socketRef.current.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error)
    })
  }

  const handleRespondToIncident = async (incidentId, status) => {
    try {
      await api.post(`/incident/${incidentId}/respond`, {
        status,
        authority_id: user.id
      })
      
      setIncidents(prev => prev.map(inc => 
        inc.id === incidentId ? { ...inc, status } : inc
      ))
      
      if (selectedIncident && selectedIncident.id === incidentId) {
        setSelectedIncident(prev => ({ ...prev, status }))
      }
      
      const statusText = status === 'acknowledged' ? '👀 Acknowledged' : 
                        status === 'en_route' ? '🚓 En Route' :
                        '✅ Resolved'
      toast.success(`${statusText}!`)
    } catch (error) {
      toast.error('Failed to update incident status')
      console.error('Error responding to incident:', error)
    }
  }

  const handleSendMessage = () => {
    if (!messageInput.trim() || !selectedIncident) return

    socketRef.current.emit('send_message', {
      incident_id: selectedIncident.id,
      message: messageInput,
      sender_name: user.name,
      sender_role: 'authority'
    })

    setChatMessages(prev => [...prev, {
      message: messageInput,
      sender_name: user.name,
      sender_role: 'authority',
      timestamp: new Date().toISOString()
    }])

    setMessageInput('')
  }

  const handleCallTourist = (phone) => {
    if (phone) {
      window.location.href = `tel:${phone}`
    } else {
      toast.error('Phone number not available')
    }
  }

  const handleSendQuickMessage = async (incidentId, message) => {
    try {
      // Send via API to trigger SMS
      await api.post(`/incident/${incidentId}/send-message`, {
        message
      })
      
      // Also send via WebSocket for real-time chat
      socketRef.current.emit('send_message', {
        incident_id: incidentId,
        message,
        sender_name: user.name,
        sender_role: 'authority'
      })

      toast.success('Quick message sent (SMS + Chat)!')
    } catch (error) {
      console.error('Error sending quick message:', error)
      toast.error('Failed to send message')
    }
  }

  const handleAddAuthority = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/add-authority', newAuthority)
      toast.success(`Authority user created successfully!`)
      setNewAuthority({ name: '', email: '', phone: '', password: '' })
      setShowAddAuthority(false)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to create authority user')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'critical': return 'border-red-600 bg-red-50'
      case 'high': return 'border-orange-600 bg-orange-50'
      case 'medium': return 'border-yellow-600 bg-yellow-50'
      default: return 'border-blue-600 bg-blue-50'
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'active': return 'bg-red-500'
      case 'acknowledged': return 'bg-yellow-500'
      case 'en_route': return 'bg-blue-500'
      case 'resolved': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Authority Command Center</h1>
          <p className="text-gray-600 mt-2">Real-time monitoring and incident response</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode(viewMode === 'map' ? 'list' : 'map')}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold"
          >
            {viewMode === 'map' ? '📋 List View' : '🗺️ Map View'}
          </button>
          <button
            onClick={() => setShowAddAuthority(!showAddAuthority)}
            className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-semibold"
          >
            ➕ Add Authority
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
          <div className="text-red-600 font-bold text-2xl">{incidents.filter(i => i.status === 'active').length}</div>
          <div className="text-gray-600 text-sm">Active Incidents</div>
        </div>
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-lg">
          <div className="text-yellow-600 font-bold text-2xl">{incidents.filter(i => i.status === 'acknowledged').length}</div>
          <div className="text-gray-600 text-sm">Acknowledged</div>
        </div>
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
          <div className="text-blue-600 font-bold text-2xl">{incidents.filter(i => i.status === 'en_route').length}</div>
          <div className="text-gray-600 text-sm">En Route</div>
        </div>
        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg">
          <div className="text-green-600 font-bold text-2xl">{incidents.filter(i => i.status === 'resolved').length}</div>
          <div className="text-gray-600 text-sm">Resolved Today</div>
        </div>
      </div>

      {/* Add Authority Form */}
      {showAddAuthority && (
        <div className="card mb-6 bg-orange-50 border-2 border-orange-200">
          <h2 className="text-2xl font-bold mb-4 text-orange-800">Add New Authority User</h2>
          <form onSubmit={handleAddAuthority} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  placeholder="Enter name"
                  value={newAuthority.name}
                  onChange={(e) => setNewAuthority({ ...newAuthority, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  placeholder="Enter email"
                  value={newAuthority.email}
                  onChange={(e) => setNewAuthority({ ...newAuthority, email: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                <input
                  type="tel"
                  placeholder="Enter phone"
                  value={newAuthority.phone}
                  onChange={(e) => setNewAuthority({ ...newAuthority, phone: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <input
                  type="password"
                  placeholder="Create password"
                  value={newAuthority.password}
                  onChange={(e) => setNewAuthority({ ...newAuthority, password: e.target.value })}
                  className="input"
                  required
                  minLength="6"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Authority User'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddAuthority(false)}
                className="btn bg-gray-300 hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Map or Incident List */}
        <div className="lg:col-span-2" key={viewMode}>
          {viewMode === 'map' ? (
            <div className="card p-0" style={{ position: 'relative', zIndex: 1 }}>
              <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 text-sm text-blue-800">
                ℹ️ Map shows only active, acknowledged, and en-route incidents. Resolved incidents are hidden.
              </div>
              <div 
                ref={mapContainerRef} 
                style={{ width: '100%', height: '600px', borderRadius: '0 0 8px 8px', position: 'relative' }}
              />
            </div>
          ) : (
            <div className="card" style={{ position: 'relative', zIndex: 1, minHeight: '600px', backgroundColor: 'white' }}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">Incident List</h2>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showResolved}
                    onChange={(e) => setShowResolved(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">Show Resolved</span>
                </label>
              </div>
              {incidents.length === 0 ? (
                <p className="text-gray-500">No incidents reported</p>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {incidents
                    .filter(incident => showResolved || incident.status !== 'resolved')
                    .map(incident => (
                    <div 
                      key={incident.id} 
                      className={`border-l-4 p-4 rounded-r-lg cursor-pointer hover:shadow-lg transition ${getPriorityColor(incident.priority)} ${selectedIncident?.id === incident.id ? 'ring-2 ring-blue-500' : ''}`}
                      onClick={() => setSelectedIncident(incident)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-lg">{incident.type.toUpperCase()}</span>
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              incident.priority === 'critical' ? 'bg-red-600 text-white' :
                              incident.priority === 'high' ? 'bg-orange-600 text-white' :
                              'bg-yellow-600 text-white'
                            }`}>
                              {incident.priority}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${getStatusColor(incident.status)}`}>
                              {incident.status}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-2">{incident.description}</p>
                          
                          {/* Tourist Contact Information */}
                          <div className="bg-white rounded p-3 mb-2 border border-gray-200">
                            <h4 className="font-semibold text-sm mb-2 text-gray-700">👤 Tourist Information:</h4>
                            {incident.user_name && (
                              <p className="text-sm text-gray-700 mb-1">
                                <strong>Name:</strong> {incident.user_name}
                              </p>
                            )}
                            {incident.user_phone && (
                              <p className="text-sm text-gray-700 mb-1">
                                <strong>📞 Phone:</strong> <a href={`tel:${incident.user_phone}`} className="text-blue-600 hover:underline">{incident.user_phone}</a>
                              </p>
                            )}
                            {incident.user_email && (
                              <p className="text-sm text-gray-700">
                                <strong>📧 Email:</strong> <a href={`mailto:${incident.user_email}`} className="text-blue-600 hover:underline">{incident.user_email}</a>
                              </p>
                            )}
                          </div>
                          
                          {incident.address && (
                            <p className="text-sm text-gray-600 mb-1">📍 <strong>Location:</strong> {incident.address}</p>
                          )}
                          
                          <p className="text-xs text-gray-500 mt-2">
                            🕐 {new Date(incident.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Selected Incident Details & Actions */}
        <div className="lg:col-span-1">
          {selectedIncident ? (
            <div className="card space-y-4">
              <div className="flex justify-between items-start">
                <h3 className="text-xl font-bold">Incident #{selectedIncident.id}</h3>
                <button 
                  onClick={() => setSelectedIncident(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2 text-sm">
                <p><strong>Type:</strong> {selectedIncident.type}</p>
                <p><strong>Status:</strong> <span className={`px-2 py-1 rounded text-white text-xs ${getStatusColor(selectedIncident.status)}`}>{selectedIncident.status}</span></p>
                <p><strong>Priority:</strong> {selectedIncident.priority}</p>
                
                {/* Tourist Information */}
                <div className="bg-blue-50 rounded p-3 mt-3 mb-3">
                  <h4 className="font-semibold mb-2">👤 Tourist Information</h4>
                  <p className="mb-1"><strong>Name:</strong> {selectedIncident.user_name || 'N/A'}</p>
                  {selectedIncident.user_phone ? (
                    <p className="mb-1">
                      <strong>📞 Phone:</strong>{' '}
                      <a href={`tel:${selectedIncident.user_phone}`} className="text-blue-600 hover:underline font-semibold">
                        {selectedIncident.user_phone}
                      </a>
                    </p>
                  ) : (
                    <p className="mb-1"><strong>📞 Phone:</strong> Not available</p>
                  )}
                  {selectedIncident.user_email ? (
                    <p>
                      <strong>📧 Email:</strong>{' '}
                      <a href={`mailto:${selectedIncident.user_email}`} className="text-blue-600 hover:underline">
                        {selectedIncident.user_email}
                      </a>
                    </p>
                  ) : (
                    <p><strong>📧 Email:</strong> Not available</p>
                  )}
                </div>
                
                {/* Location with Get Directions button */}
                <div className="bg-green-50 rounded p-3 mt-3">
                  <h4 className="font-semibold mb-2">📍 Location</h4>
                  <p className="mb-2">{selectedIncident.address || 'Location detected'}</p>
                  {selectedIncident.location && selectedIncident.location.latitude && selectedIncident.location.longitude && (
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${selectedIncident.location.latitude},${selectedIncident.location.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-semibold text-sm text-center"
                    >
                      🧭 Get Directions to Emergency
                    </a>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Quick Actions</h4>
                <div className="space-y-2">
                  <button
                    onClick={() => handleCallTourist(selectedIncident.user_phone)}
                    className="w-full px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded font-semibold text-sm"
                  >
                    📞 Call Tourist
                  </button>
                  
                  {selectedIncident.status === 'active' && (
                    <>
                      <button
                        onClick={() => handleRespondToIncident(selectedIncident.id, 'acknowledged')}
                        className="w-full px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded font-semibold text-sm"
                      >
                        👀 Acknowledge
                      </button>
                      <button
                        onClick={() => handleRespondToIncident(selectedIncident.id, 'en_route')}
                        className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded font-semibold text-sm"
                      >
                        🚓 En Route
                      </button>
                    </>
                  )}
                  
                  {selectedIncident.status === 'acknowledged' && (
                    <button
                      onClick={() => handleRespondToIncident(selectedIncident.id, 'en_route')}
                      className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded font-semibold text-sm"
                    >
                      🚓 En Route
                    </button>
                  )}
                  
                  {(selectedIncident.status === 'acknowledged' || selectedIncident.status === 'en_route') && (
                    <button
                      onClick={() => handleRespondToIncident(selectedIncident.id, 'resolved')}
                      className="w-full px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded font-semibold text-sm"
                    >
                      ✅ Mark Resolved
                    </button>
                  )}
                </div>
              </div>

              {/* Quick Messages */}
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Quick Messages</h4>
                <div className="space-y-2">
                  <button
                    onClick={() => handleSendQuickMessage(selectedIncident.id, '🚓 Help is on the way! ETA: 5 minutes')}
                    className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm text-left"
                  >
                    🚓 ETA 5 minutes
                  </button>
                  <button
                    onClick={() => handleSendQuickMessage(selectedIncident.id, '👀 We have received your alert. Stay calm, help is coming.')}
                    className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm text-left"
                  >
                    👀 Alert received
                  </button>
                  <button
                    onClick={() => handleSendQuickMessage(selectedIncident.id, '📍 Can you provide more details about your location?')}
                    className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm text-left"
                  >
                    📍 Need location details
                  </button>
                  <button
                    onClick={() => handleSendQuickMessage(selectedIncident.id, '🆘 Stay where you are. Do not move. Help is arriving shortly.')}
                    className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm text-left"
                  >
                    🆘 Stay in place
                  </button>
                </div>
              </div>

              {/* Chat */}
              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-semibold">Chat with Tourist</h4>
                  <button 
                    onClick={() => {
                      setShowChat(!showChat)
                      if (!showChat && selectedIncident) {
                        socketRef.current.emit('join_incident_room', { incident_id: selectedIncident.id })
                      }
                    }}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                  >
                    {showChat ? 'Hide' : 'Show'} Chat
                  </button>
                </div>
                
                {showChat && (
                  <div className="space-y-3">
                    <div className="bg-gray-50 rounded p-3 h-40 overflow-y-auto space-y-2">
                      {chatMessages.length === 0 ? (
                        <p className="text-gray-500 text-sm text-center">No messages yet</p>
                      ) : (
                        chatMessages.map((msg, idx) => (
                          <div key={idx} className={`text-sm ${msg.sender_role === 'authority' ? 'text-right' : 'text-left'}`}>
                            <div className={`inline-block px-3 py-2 rounded ${msg.sender_role === 'authority' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}>
                              <p className="font-semibold text-xs mb-1">{msg.sender_name}</p>
                              <p>{msg.message}</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Type message..."
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        className="flex-1 px-3 py-2 border rounded text-sm"
                      />
                      <button
                        onClick={handleSendMessage}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded font-semibold text-sm"
                      >
                        Send
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <p className="text-gray-500 text-center py-8">
                Select an incident to view details and take action
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
