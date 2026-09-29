import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage/LandingPage';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import RiderDashboard from './pages/Dashboard/RiderDashboard';
import DriverDashboard from './pages/Dashboard/DriverDashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route 
        path="/rider-dashboard" 
        element={
          <ProtectedRoute allowedRole="rider">
            <RiderDashboard />
          </ProtectedRoute>
        } 
      />
      <Route  
        path="/driver-dashboard" 
        element={
          <ProtectedRoute allowedRole="driver">
            <DriverDashboard />
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

export default App;
