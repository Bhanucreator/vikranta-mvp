import axios from 'axios'

// Get API URL from environment, ensure it ends with /api
let API_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// If the URL doesn't end with /api, append it
if (API_URL && !API_URL.endsWith('/api')) {
  API_URL = API_URL.replace(/\/$/, '') + '/api'
}

console.log('🔗 API Base URL:', API_URL)

const api = axios.create({
  baseURL: API_URL,
  headers: {'Content-Type': 'application/json'}
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, (error) => Promise.reject(error))

api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }
  return Promise.reject(error)
})

export default api