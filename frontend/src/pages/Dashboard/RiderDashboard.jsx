import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const RiderDashboard = () => {
  const [pickup, setPickup] = useState('');
  const [dropoff, setDropoff] = useState('');
  const [vehicle, setVehicle] = useState('car');
  const [isSearching, setIsSearching] = useState(false);

  const handleRequestRide = (e) => {
    e.preventDefault();
    if (!pickup || !dropoff) return;
    
    setIsSearching(true);
    
    // Simulate searching for a driver
    setTimeout(() => {
      setIsSearching(false);
      alert('Drivers found! Initiating bidding process...');
    }, 3000);
  };

  const vehicleOptions = [
    { id: 'bike', label: 'MOTO', icon: '🏍️', price: '₹50 - ₹70', time: '2 min' },
    { id: 'auto', label: 'AUTO', icon: '🛺', price: '₹80 - ₹110', time: '4 min' },
    { id: 'car', label: 'CAB', icon: '🚗', price: '₹150 - ₹200', time: '5 min' },
  ];

  return (
    <div className="min-h-screen bg-ridebid-black flex flex-col font-sans selection:bg-ridebid-green selection:text-black text-white">
      {/* Decorative Grid Background */}
      <div className="fixed inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      {/* Top Navbar */}
      <header className="relative z-20 bg-black border-b-2 border-white p-4 flex justify-between items-center brutal-shadow-white sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-ridebid-green flex items-center justify-center font-bold text-black transform -skew-x-12">
            RB
          </div>
          <span className="text-xl font-bold tracking-widest text-white uppercase">
            RIDEBID / RIDER
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 border-2 border-ridebid-green px-3 py-1 font-mono text-xs">
            <span className="w-2 h-2 bg-ridebid-green rounded-full animate-pulse"></span>
            NETWORK ONLINE
          </div>
          <Link to="/" className="bg-white text-black font-bold uppercase tracking-widest px-4 py-1 brutal-shadow-hover transition-all border-2 border-transparent hover:border-black font-mono text-sm">
            LOGOUT
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row relative z-10 p-4 lg:p-6 gap-6 lg:h-[calc(100vh-76px)]">
        
        {/* Left Side: Ride Booking Panel */}
        <div className="w-full lg:w-[400px] flex flex-col gap-6 lg:h-full lg:overflow-y-auto pb-6 custom-scrollbar">
          
          <div className="bg-black border-2 border-white brutal-shadow">
            <div className="bg-white p-2 border-b-2 border-white flex justify-between items-center">
              <span className="text-black font-mono text-xs font-bold uppercase tracking-widest">
                book_ride.exe
              </span>
              <div className="flex gap-1">
                <div className="w-3 h-3 border-2 border-black bg-black"></div>
                <div className="w-3 h-3 border-2 border-black bg-ridebid-green"></div>
              </div>
            </div>
            
            <div className="p-6">
              <h2 className="text-2xl font-extrabold uppercase mb-6 tracking-tight">
                WHERE TO?
              </h2>

              <form onSubmit={handleRequestRide} className="flex flex-col gap-5">
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-black"></div>
                  <input 
                    type="text" 
                    placeholder="ENTER PICKUP LOCATION"
                    value={pickup}
                    onChange={(e) => setPickup(e.target.value)}
                    className="w-full bg-transparent border-2 border-gray-600 text-white p-3 pl-10 font-mono text-sm focus:outline-none focus:border-ridebid-green focus:bg-gray-900 transition-colors uppercase placeholder-gray-600"
                    required
                  />
                  {/* Connecting Line */}
                  <div className="absolute left-[21px] top-[calc(100%-8px)] h-8 border-l-2 border-dashed border-gray-600 z-10"></div>
                </div>

                <div className="relative mt-2">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 w-3 h-3 bg-ridebid-green border-2 border-black"></div>
                  <input 
                    type="text" 
                    placeholder="ENTER DROP-OFF LOCATION"
                    value={dropoff}
                    onChange={(e) => setDropoff(e.target.value)}
                    className="w-full bg-transparent border-2 border-gray-600 text-white p-3 pl-10 font-mono text-sm focus:outline-none focus:border-ridebid-green focus:bg-gray-900 transition-colors uppercase placeholder-gray-600"
                    required
                  />
                </div>

                {pickup && dropoff && (
                  <div className="mt-6 animate-fade-in">
                    <h3 className="font-mono text-xs font-bold text-gray-400 mb-3 tracking-widest">SELECT VEHICLE</h3>
                    <div className="flex flex-col gap-3">
                      {vehicleOptions.map((opt) => (
                        <div 
                          key={opt.id}
                          onClick={() => setVehicle(opt.id)}
                          className={`
                            border-2 p-3 flex items-center justify-between cursor-pointer transition-all
                            ${vehicle === opt.id 
                              ? 'border-ridebid-green bg-gray-900 brutal-shadow' 
                              : 'border-gray-800 hover:border-gray-600 bg-black'}
                          `}
                        >
                          <div className="flex items-center gap-4">
                            <span className="text-2xl">{opt.icon}</span>
                            <div className="flex flex-col">
                              <span className="font-bold uppercase tracking-wider">{opt.label}</span>
                              <span className="font-mono text-xs text-ridebid-green">{opt.time} away</span>
                            </div>
                          </div>
                          <span className="font-mono font-bold">{opt.price}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 p-4 bg-gray-900 border-2 border-ridebid-green border-dashed">
                      <div className="flex justify-between items-center font-mono text-sm mb-2">
                        <span className="text-gray-400">ESTIMATED FARE</span>
                        <span className="font-bold text-ridebid-green">{vehicleOptions.find(v => v.id === vehicle)?.price}</span>
                      </div>
                      <p className="text-[10px] text-gray-500 font-mono">Final price determined by driver bidding system.</p>
                    </div>

                    <button 
                      type="submit"
                      disabled={isSearching}
                      className="w-full mt-6 bg-ridebid-green text-black font-bold uppercase tracking-widest px-6 py-4 brutal-shadow-white transition-all border-2 border-transparent hover:border-white font-mono disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden"
                    >
                      <span className="relative z-10">{isSearching ? 'BROADCASTING REQUEST...' : 'REQUEST RIDE'}</span>
                      {isSearching && (
                        <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                      )}
                    </button>
                  </div>
                )}
              </form>
            </div>
          </div>

          {/* Quick Actions / Recent Places */}
          <div className="bg-black border-2 border-gray-800 p-4">
            <h3 className="font-mono text-xs font-bold text-gray-400 mb-3 tracking-widest">RECENT LOCATIONS</h3>
            <div className="flex flex-col gap-2">
              <button className="text-left font-mono text-sm border border-gray-800 p-2 hover:bg-gray-900 hover:border-ridebid-green transition-colors uppercase truncate flex items-center gap-2">
                <span className="text-ridebid-green">★</span> Home
              </button>
              <button className="text-left font-mono text-sm border border-gray-800 p-2 hover:bg-gray-900 hover:border-ridebid-green transition-colors uppercase truncate flex items-center gap-2">
                <span className="text-ridebid-green">✦</span> Work / Tech Park
              </button>
              <button className="text-left font-mono text-sm border border-gray-800 p-2 hover:bg-gray-900 hover:border-ridebid-green transition-colors uppercase truncate flex items-center gap-2">
                <span className="text-gray-600">⌚</span> Central Station
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Map Area (Simulated for Brutalist design) */}
        <div className="flex-1 bg-[#111] border-2 border-white brutal-shadow relative overflow-hidden min-h-[400px] lg:min-h-0 group">
          {/* Faux Map Grid Pattern */}
          <div className="absolute inset-0 opacity-20 pointer-events-none" 
               style={{ backgroundImage: 'linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000), linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000)', backgroundSize: '60px 60px', backgroundPosition: '0 0, 30px 30px' }}>
          </div>
          
          {/* Map Overlay UI */}
          <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
            <div className="bg-black border-2 border-white px-3 py-1 font-mono text-xs brutal-shadow-white pointer-events-auto">
              MAP_DATA_STREAM :: ACTIVE
            </div>
            <div className="flex flex-col gap-2 pointer-events-auto">
              <button className="w-10 h-10 bg-white text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center text-xl hover:bg-gray-200">
                +
              </button>
              <button className="w-10 h-10 bg-white text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center text-xl hover:bg-gray-200">
                -
              </button>
              <button className="w-10 h-10 mt-4 bg-ridebid-green text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center hover:bg-green-400">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
                </svg>
              </button>
            </div>
          </div>

          {/* Central Map Marker (Faux) */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
            <div className="bg-black text-white font-mono text-xs px-2 py-1 border border-ridebid-green mb-1 whitespace-nowrap animate-pulse">
              {pickup ? 'CURRENT ORIGIN' : 'LOCATING...'}
            </div>
            <div className="w-4 h-4 bg-ridebid-green border-2 border-white rotate-45 transform origin-center shadow-[0_0_15px_#4f772d]"></div>
            <div className="w-1 h-8 bg-gradient-to-b from-ridebid-green to-transparent"></div>
            <div className="w-8 h-2 bg-black/50 blur rounded-full mt-1"></div>
          </div>
          
          {/* Random moving blips simulating cars */}
          {pickup && (
            <>
              <div className="absolute top-1/4 left-1/3 w-3 h-3 bg-yellow-400 border border-black animate-pulse" style={{ animationDuration: '3s' }}></div>
              <div className="absolute bottom-1/3 right-1/4 w-3 h-3 bg-yellow-400 border border-black animate-pulse" style={{ animationDuration: '2s' }}></div>
              <div className="absolute top-2/3 left-1/4 w-3 h-3 bg-yellow-400 border border-black animate-pulse" style={{ animationDuration: '4s' }}></div>
            </>
          )}

          {isSearching && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-30">
              <div className="bg-black border-2 border-ridebid-green p-8 max-w-sm w-full mx-4 text-center brutal-shadow">
                <div className="w-12 h-12 border-4 border-gray-800 border-t-ridebid-green rounded-full animate-spin mx-auto mb-6"></div>
                <h3 className="text-xl font-bold uppercase mb-2">Finding Drivers</h3>
                <p className="font-mono text-sm text-gray-400">Broadcasting your request to the network...</p>
                <button 
                  onClick={() => setIsSearching(false)}
                  className="mt-6 border-b-2 border-red-500 text-red-500 font-mono text-xs uppercase hover:text-red-400 transition-colors pb-1"
                >
                  ABORT REQUEST
                </button>
              </div>
            </div>
          )}
        </div>

      </main>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #000;
          border-left: 1px solid #333;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #4f772d;
        }
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out forwards;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default RiderDashboard;
