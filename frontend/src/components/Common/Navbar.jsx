import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="bg-vikranta-blue text-white shadow-lg fixed top-0 w-full z-50">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold">VIKRANTA</Link>
        <div className="flex items-center space-x-4">
          <span className="text-sm">{user?.name}</span>
          <button onClick={logout} className="btn btn-primary">
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}