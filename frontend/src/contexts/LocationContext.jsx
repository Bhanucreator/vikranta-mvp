import React, { createContext, useContext, useState } from 'react'

const LocationContext = createContext()

export const useLocation = () => {
  const context = useContext(LocationContext)
  if (!context) throw new Error('useLocation must be used within LocationProvider')
  return context
}

export const LocationProvider = ({ children }) => {
  const [currentLocation, setCurrentLocation] = useState(null)
  const [tracking, setTracking] = useState(false)
  
  const value = { currentLocation, tracking, setTracking, setCurrentLocation }
  
  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  )
}