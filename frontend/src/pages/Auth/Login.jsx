import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
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
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/users/login/', formData);
      
      // Store tokens and user info in localStorage
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
        // Display backend error messages
        const errorData = err.response.data;
        const errorMessage = errorData.non_field_errors 
          ? errorData.non_field_errors[0] 
          : 'Invalid login credentials.';
        setError(errorMessage);
      } else {
        setError('Failed to connect to the server.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ridebid-black flex items-center justify-center p-4">
      {/* Decorative Grid Background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      <div className="w-full max-w-md relative z-10">
        
        {/* Status Sticker */}
        <div className="absolute -right-4 -top-6 z-30 transform rotate-6">
          <div className="bg-ridebid-green border-2 border-black p-2 text-center w-24 brutal-shadow-white">
            <div className="text-[10px] font-mono text-black font-bold tracking-widest uppercase">Secure</div>
          </div>
        </div>

        <div className="bg-black border-2 border-ridebid-green brutal-shadow w-full">
          {/* Window Header */}
          <div className="bg-ridebid-green p-3 flex items-center justify-between border-b-2 border-ridebid-green">
            <div className="flex gap-2">
              <div className="w-3 h-3 border-2 border-black bg-white"></div>
              <div className="w-3 h-3 border-2 border-black bg-black"></div>
            </div>
            <div className="text-black font-mono text-xs font-bold uppercase tracking-widest">
              login.exe
            </div>
            <div className="text-black font-bold font-mono border-2 border-black px-1 leading-none hover:bg-black hover:text-ridebid-green cursor-pointer">
              X
            </div>
          </div>
          
          {/* Window Body */}
          <div className="p-8">
            <div className="mb-8">
              <h1 className="text-4xl font-extrabold uppercase text-white font-sans tracking-tight">
                WELCOME <br />
                <span className="text-ridebid-green">BACK.</span>
              </h1>
            </div>

            {error && (
              <div className="bg-red-500 text-white font-mono text-xs p-3 mb-6 border-2 border-white brutal-shadow-white uppercase">
                ERROR: {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              
              <div className="flex flex-col gap-2">
                <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                  Username
                </label>
                <input 
                  type="text" 
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className="bg-transparent border-2 border-white text-white p-3 font-mono focus:outline-none focus:border-ridebid-green focus:ring-0 placeholder-gray-600 transition-colors"
                  placeholder="_enter_username"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-white font-mono text-xs font-bold tracking-widest uppercase">
                  Password
                </label>
                <input 
                  type="password" 
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="bg-transparent border-2 border-white text-white p-3 font-mono focus:outline-none focus:border-ridebid-green focus:ring-0 placeholder-gray-600 transition-colors"
                  placeholder="********"
                />
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="mt-4 bg-white text-black font-bold uppercase tracking-widest px-6 py-4 brutal-shadow-hover transition-all border-2 border-transparent hover:border-black font-mono disabled:opacity-50"
              >
                {isLoading ? 'Processing...' : 'Access Terminal'}
              </button>

            </form>

            <div className="mt-8 text-center border-t-2 border-gray-800 pt-6">
              <p className="text-gray-400 font-mono text-xs">
                NEW USER? <Link to="/register" className="text-ridebid-green hover:text-white transition-colors underline decoration-2 underline-offset-4">INITIALIZE ACCOUNT</Link>
              </p>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
