import React from 'react';
import { Navigate } from 'react-router-dom';


const ProtectedRoute = ({ children, allowedRole = 'any' }) => {
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');

  if (!token || !userStr) {
    return <Navigate to="/login" replace />;
  }

  try {
    const user = JSON.parse(userStr);

    if (allowedRole !== 'any') {
      const isRider = user.role === 'rider' || user.role === 'rider_driver';
      const isDriver = user.role === 'driver' || user.role === 'rider_driver';

      if (allowedRole === 'rider' && !isRider) {
        // Driver trying to access rider pages
        return <Navigate to="/driver-dashboard" replace />;
      }

      if (allowedRole === 'driver' && !isDriver) {
        // Rider trying to access driver pages
        return <Navigate to="/rider-dashboard" replace />;
      }
    }

    // User is authorized
    return children;
  } catch (error) {
    // Malformed user data, clear and force re-login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    return <Navigate to="/login" replace />;
  }
};

export default ProtectedRoute;
