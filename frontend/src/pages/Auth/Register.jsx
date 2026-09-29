import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    role: 'rider', // default role
    phone: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault(); 
    setError('');
    
    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/users/register/', formData);
      
      // Store tokens and user info (Auto-login after register)
      const user = response.data.user;
      localStorage.setItem('access_token', response.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.tokens.refresh);
      localStorage.setItem('user', JSON.stringify(user));

      // Redirect to correct dashboard based on role
      if (user.role === 'driver') {
        navigate('/driver-dashboard');
      } else {
        navigate('/rider-dashboard');
      }
    } catch (err) {
      if (err.response && err.response.data) {
        // Backend returns a dictionary of field errors or non_field_errors
        const errorData = err.response.data;
        
        // Extract the first error message available to display
        const firstErrorKey = Object.keys(errorData)[0];
        const errorMessage = errorData[firstErrorKey];
        
        // If it's an array of errors for that field, show the first one
        if (Array.isArray(errorMessage)) {
          setError(`${firstErrorKey.toUpperCase()}: ${errorMessage[0]}`);
        } else {
          setError(errorMessage.toString());
        }
      } else {
        setError('Failed to connect to the server.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ridebid-black flex items-center justify-center p-4 py-12">
      {/* Decorative Grid Background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      <div className="w-full max-w-xl relative z-10">
        
        <div className="bg-black border-2 border-white brutal-shadow w-full">
          {/* Window Header */}
          <div className="bg-white p-3 flex items-center justify-between border-b-2 border-white">
            <div className="flex gap-2">
              <div className="w-3 h-3 border-2 border-black bg-ridebid-green"></div>
              <div className="w-3 h-3 border-2 border-black bg-black"></div>
            </div>
            <div className="text-black font-mono text-xs font-bold uppercase tracking-widest">
              register_user.sh
            </div>
            <div className="text-black font-bold font-mono border-2 border-black px-1 leading-none hover:bg-black hover:text-white cursor-pointer transition-colors">
              X
            </div>
          </div>
          
          {/* Window Body */}
          <div className="p-8">
            <div className="mb-6">
              <h1 className="text-3xl font-extrabold uppercase text-white font-sans tracking-tight">
                INITIALIZE <br />
                <span className="bg-ridebid-green text-black px-2 inline-block mt-2 transform -rotate-1">
                  NEW ACCOUNT.
                </span>
              </h1>
            </div>

            {error && (
              <div className="bg-red-500 text-white font-mono text-xs p-3 mb-6 border-2 border-white brutal-shadow-white">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="flex flex-col gap-2">
                  <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                    Username *
                  </label>
                  <input 
                    type="text" 
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                    className="bg-transparent border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                    Email *
                  </label>
                  <input 
                    type="email" 
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="bg-transparent border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                  Phone Number
                </label>
                <input 
                  type="text" 
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="bg-transparent border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                  placeholder="+1234567890"
                />
              </div>
              
              <div className="flex flex-col gap-2">
                <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                  Role *
                </label>
                <select 
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="bg-black border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                >
                  <option value="rider">RIDER (Book Rides)</option>
                  <option value="driver">DRIVER (Offer Rides)</option>
                  <option value="rider_driver">BOTH (Rider & Driver)</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-2">
                <div className="flex flex-col gap-2">
                  <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                    Password *
                  </label>
                  <input 
                    type="password" 
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="bg-transparent border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                    Confirm Password *
                  </label>
                  <input 
                    type="password" 
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    required
                    className="bg-transparent border-2 border-gray-600 text-white p-2.5 font-mono focus:outline-none focus:border-white focus:ring-0 transition-colors"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="mt-6 bg-ridebid-green text-black font-bold uppercase tracking-widest px-6 py-4 brutal-shadow-white transition-all border-2 border-transparent hover:border-white font-mono disabled:opacity-50"
              >
                {isLoading ? 'Compiling...' : 'Execute Registration'}
              </button>

            </form>

            <div className="mt-8 text-center border-t-2 border-gray-800 pt-6">
              <p className="text-gray-400 font-mono text-xs uppercase">
                ALREADY IN THE SYSTEM? <Link to="/login" className="text-white hover:text-ridebid-green transition-colors underline decoration-2 underline-offset-4">LOGIN HERE</Link>
              </p>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
