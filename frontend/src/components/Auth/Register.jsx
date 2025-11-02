import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authService } from '../../services/auth'
import { toast } from 'react-toastify'

export default function Register() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    emergency_contact: '',
    role: 'tourist'
  })
  const [loading, setLoading] = useState(false)
  const [showOtpField, setShowOtpField] = useState(false)
  const [otp, setOtp] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await authService.register(formData)
      setEmailSent(response.email_sent || false)
      if (response.email_sent) {
        toast.success('Registration successful! OTP sent to your email')
      } else {
        toast.warning('Registration successful! Email failed - check backend logs for OTP')
      }
      setShowOtpField(true)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleOtpSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authService.verifyOTP(formData.email, otp)
      toast.success('Email verified! You can now login')
      navigate('/login')
    } catch (error) {
      toast.error(error.response?.data?.error || 'OTP verification failed')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  if (showOtpField) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-vikranta-blue to-vikranta-green p-4">
        <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
          <h2 className="text-3xl font-bold text-center mb-2 text-vikranta-blue">Verify Email</h2>
          <p className="text-center text-gray-600 mb-6 text-sm">Enter the OTP sent to {formData.email}</p>
          
          <form onSubmit={handleOtpSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">OTP Code</label>
              <input
                type="text"
                placeholder="Enter 6-digit OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="input text-center text-2xl tracking-widest"
                maxLength="6"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-full" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify & Complete Registration'}
            </button>
          </form>

          <div className={`mt-6 p-4 rounded-lg border-2 ${emailSent ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
            {emailSent ? (
              <div className="text-center">
                <p className="text-sm text-green-800 font-medium mb-2">
                  ✅ OTP sent to your email successfully!
                </p>
                <p className="text-xs text-green-700">
                  Check your inbox (and spam folder) for the verification code.
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-yellow-800 font-medium mb-2">
                  ⚠️ Email sending failed
                </p>
                <p className="text-xs text-yellow-700 mb-2">
                  Check backend logs for OTP:
                </p>
                <code className="block text-xs bg-yellow-100 p-2 rounded">
                  docker-compose logs backend | grep OTP
                </code>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-vikranta-blue to-vikranta-green p-4">
      <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <h2 className="text-3xl font-bold text-center mb-2 text-vikranta-blue">Register as Tourist</h2>
        <p className="text-center text-gray-600 mb-6 text-sm">Create your VIKRANTA tourist account</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
            <input
              type="text"
              name="name"
              placeholder="Enter your full name"
              value={formData.name}
              onChange={handleChange}
              className="input"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              className="input"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              name="phone"
              placeholder="Enter your phone number"
              value={formData.phone}
              onChange={handleChange}
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact *</label>
            <input
              type="tel"
              name="emergency_contact"
              placeholder="Emergency contact number"
              value={formData.emergency_contact}
              onChange={handleChange}
              className="input"
              required
            />
            <p className="text-xs text-gray-500 mt-1">This will be contacted in case of emergency</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
            <input
              type="password"
              name="password"
              placeholder="Create a password (min 6 characters)"
              value={formData.password}
              onChange={handleChange}
              className="input"
              required
              minLength="6"
            />
          </div>
          <button type="submit" className="btn btn-primary w-full" disabled={loading}>
            {loading ? 'Registering...' : '🧳 Register as Tourist'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Already have an account? <Link to="/login" className="text-vikranta-orange font-semibold hover:underline">Login</Link>
        </p>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-800">
            <strong>👮 Authority Registration:</strong> Authority accounts can only be created by existing authorities from the dashboard.
          </p>
        </div>
      </div>
    </div>
  )
}