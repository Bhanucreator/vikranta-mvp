import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { toast } from 'react-toastify'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginType, setLoginType] = useState('tourist')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast.success('Login successful!')
      navigate('/')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-vikranta-orange to-vikranta-blue p-4">
      <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <h2 className="text-3xl font-bold text-center mb-2 text-vikranta-blue">VIKRANTA</h2>
        <p className="text-center text-gray-600 mb-6 text-sm">Smart Tourist Safety System</p>
        
        {/* Login Type Selector */}
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setLoginType('tourist')}
            className={`flex-1 py-2 rounded-lg font-medium transition-all ${
              loginType === 'tourist'
                ? 'bg-vikranta-blue text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            🧳 Tourist
          </button>
          <button
            type="button"
            onClick={() => setLoginType('authority')}
            className={`flex-1 py-2 rounded-lg font-medium transition-all ${
              loginType === 'authority'
                ? 'bg-vikranta-orange text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            👮 Authority
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
            />
          </div>
          <button type="submit" className="btn btn-primary w-full" disabled={loading}>
            {loading ? 'Logging in...' : `Login as ${loginType === 'tourist' ? 'Tourist' : 'Authority'}`}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Don't have an account? <Link to="/register" className="text-vikranta-orange font-semibold hover:underline">Register as Tourist</Link>
        </p>

        {loginType === 'authority' && (
          <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
            <p className="text-xs text-orange-800 text-center">
              <strong>👮 Authority Login:</strong><br/>
              Use credentials provided by your admin
            </p>
          </div>
        )}
      </div>
    </div>
  )
}