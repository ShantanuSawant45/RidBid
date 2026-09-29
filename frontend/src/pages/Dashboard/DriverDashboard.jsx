import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const DriverDashboard = () => {
  const [isOnline, setIsOnline] = useState(false);
  const [biddingOn, setBiddingOn] = useState(null);
  const [bidAmount, setBidAmount] = useState('');

  // Simulated incoming ride requests
  const [rideRequests, setRideRequests] = useState([
    { id: 1, pickup: 'Central Station', dropoff: 'Tech Park', distance: '4.2 km', estFare: '₹120', time: '10 mins ago', status: 'pending' },
    { id: 2, pickup: 'Airport Terminal 1', dropoff: 'Downtown Hotel', distance: '15.5 km', estFare: '₹450', time: 'Just now', status: 'pending' },
  ]);

  const handleToggleStatus = () => {
    setIsOnline(!isOnline);
  };

  const handleBidSubmit = (e, rideId) => {
    e.preventDefault();
    if (!bidAmount) return;

    // Simulate placing a bid
    setRideRequests(prev => prev.map(ride => 
      ride.id === rideId ? { ...ride, status: 'bidded', myBid: bidAmount } : ride
    ));
    setBiddingOn(null);
    setBidAmount('');
    alert(`Bid of ₹${bidAmount} placed successfully! Waiting for rider to accept...`);
  };

  return (
    <div className="min-h-screen bg-ridebid-black flex flex-col font-sans selection:bg-ridebid-green selection:text-black text-white">
      {/* Decorative Grid Background */}
      <div className="fixed inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      {/* Top Navbar */}
      <header className="relative z-20 bg-black border-b-2 border-white p-4 flex justify-between items-center brutal-shadow-white sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white flex items-center justify-center font-bold text-black transform -skew-x-12">
            RB
          </div>
          <span className="text-xl font-bold tracking-widest text-white uppercase flex items-center gap-2">
            RIDEBID <span className="text-gray-500">/</span> <span className="text-ridebid-green">DRIVER</span>
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={handleToggleStatus}
            className={`hidden md:flex items-center gap-2 border-2 px-4 py-1 font-mono text-xs font-bold transition-all brutal-shadow-hover
              ${isOnline ? 'border-ridebid-green bg-ridebid-green text-black' : 'border-gray-500 text-gray-500 hover:border-white hover:text-white'}`}
          >
            {isOnline ? (
              <><span className="w-2 h-2 bg-black rounded-full animate-pulse"></span> ONLINE & RECEIVING</>
            ) : (
              <><span className="w-2 h-2 bg-gray-500 rounded-full"></span> OFFLINE</>
            )}
          </button>
          <Link to="/" className="bg-white text-black font-bold uppercase tracking-widest px-4 py-1 brutal-shadow-hover transition-all border-2 border-transparent hover:border-black font-mono text-sm">
            LOGOUT
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row relative z-10 p-4 lg:p-6 gap-6 lg:h-[calc(100vh-76px)]">
        
        {/* Left Side: Requests & Stats */}
        <div className="w-full lg:w-[450px] flex flex-col gap-6 lg:h-full lg:overflow-y-auto pb-6 custom-scrollbar">
          
          {/* Driver Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black border-2 border-white p-4 brutal-shadow group hover:-translate-y-1 transition-transform">
              <div className="font-mono text-xs text-gray-400 mb-1 tracking-widest uppercase">TODAY'S EARNINGS</div>
              <div className="text-3xl font-bold text-ridebid-green">₹1,240</div>
              <div className="font-mono text-[10px] text-gray-500 mt-2">6 TRIPS COMPLETED</div>
            </div>
            <div className="bg-black border-2 border-white p-4 brutal-shadow group hover:-translate-y-1 transition-transform">
              <div className="font-mono text-xs text-gray-400 mb-1 tracking-widest uppercase">RATING</div>
              <div className="text-3xl font-bold">4.9<span className="text-ridebid-green text-xl">★</span></div>
              <div className="font-mono text-[10px] text-gray-500 mt-2">124 TOTAL REVIEWS</div>
            </div>
          </div>

          {/* Incoming Requests Panel */}
          <div className="bg-black border-2 border-white brutal-shadow flex-1 flex flex-col">
            <div className="bg-white p-2 border-b-2 border-white flex justify-between items-center sticky top-0 z-10">
              <span className="text-black font-mono text-xs font-bold uppercase tracking-widest">
                incoming_requests.exe
              </span>
              <div className="flex gap-2 font-mono text-[10px] text-black">
                {isOnline ? 'SCANNING...' : 'PAUSED'}
              </div>
            </div>
            
            <div className="p-4 flex-1">
              {!isOnline ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-gray-700">
                  <div className="text-4xl mb-4">😴</div>
                  <h3 className="text-xl font-bold uppercase mb-2 text-gray-500">You are offline</h3>
                  <p className="font-mono text-sm text-gray-600 mb-6">Toggle your status to online to start receiving ride requests in your area.</p>
                  <button 
                    onClick={handleToggleStatus}
                    className="bg-white text-black font-bold uppercase px-6 py-3 border-2 border-black brutal-shadow-hover hover:bg-gray-200 transition-colors"
                  >
                    GO ONLINE
                  </button>
                </div>
              ) : rideRequests.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="w-12 h-12 border-4 border-gray-800 border-t-ridebid-green rounded-full animate-spin mx-auto mb-6"></div>
                  <h3 className="text-xl font-bold uppercase mb-2">Searching...</h3>
                  <p className="font-mono text-sm text-gray-500">Waiting for riders nearby.</p>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {rideRequests.map(ride => (
                    <div key={ride.id} className="border-2 border-gray-700 bg-gray-900 overflow-hidden group hover:border-ridebid-green transition-colors">
                      {/* Request Header */}
                      <div className="p-3 border-b-2 border-gray-800 flex justify-between items-center bg-black">
                        <span className="font-mono text-xs text-ridebid-green animate-pulse">{ride.time}</span>
                        <span className="font-mono text-xs font-bold bg-white text-black px-2 py-1">{ride.distance}</span>
                      </div>
                      
                      {/* Locations */}
                      <div className="p-4 flex flex-col gap-3">
                        <div className="flex items-start gap-3">
                          <div className="w-3 h-3 bg-white border-2 border-black mt-1 flex-shrink-0"></div>
                          <div className="flex-1 font-mono text-sm uppercase truncate">{ride.pickup}</div>
                        </div>
                        <div className="ml-[5px] h-4 border-l-2 border-dashed border-gray-600"></div>
                        <div className="flex items-start gap-3">
                          <div className="w-3 h-3 bg-ridebid-green border-2 border-black mt-1 flex-shrink-0"></div>
                          <div className="flex-1 font-mono text-sm uppercase truncate">{ride.dropoff}</div>
                        </div>
                      </div>

                      {/* Action Area */}
                      <div className="p-4 bg-black border-t-2 border-gray-800">
                        {ride.status === 'bidded' ? (
                          <div className="flex justify-between items-center">
                            <span className="font-mono text-sm text-gray-400">YOUR BID: <strong className="text-white">₹{ride.myBid}</strong></span>
                            <span className="text-ridebid-green font-bold text-sm uppercase">WAITING FOR RIDER...</span>
                          </div>
                        ) : biddingOn === ride.id ? (
                          <form onSubmit={(e) => handleBidSubmit(e, ride.id)} className="flex gap-2">
                            <div className="relative flex-1">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-mono">₹</span>
                              <input 
                                type="number" 
                                value={bidAmount}
                                onChange={(e) => setBidAmount(e.target.value)}
                                placeholder={ride.estFare.replace('₹', '')}
                                className="w-full bg-gray-900 border-2 border-ridebid-green text-white p-2 pl-7 font-mono focus:outline-none"
                                required
                                autoFocus
                              />
                            </div>
                            <button type="submit" className="bg-ridebid-green text-black font-bold px-4 border-2 border-ridebid-green hover:bg-green-500">
                              SEND
                            </button>
                            <button type="button" onClick={() => setBiddingOn(null)} className="bg-transparent text-gray-500 border-2 border-gray-700 px-3 hover:text-white hover:border-white">
                              ✕
                            </button>
                          </form>
                        ) : (
                          <div className="flex gap-2">
                            <button 
                              onClick={() => { setBiddingOn(ride.id); setBidAmount(ride.estFare.replace('₹', '')); }}
                              className="flex-1 bg-white text-black font-bold uppercase py-2 border-2 border-white hover:bg-gray-200 transition-colors text-sm"
                            >
                              BID (Est. {ride.estFare})
                            </button>
                            <button 
                              onClick={() => setRideRequests(prev => prev.filter(r => r.id !== ride.id))}
                              className="bg-transparent text-gray-500 border-2 border-gray-700 px-4 font-bold hover:text-white hover:border-white transition-colors"
                            >
                              DECLINE
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Map Area */}
        <div className="flex-1 bg-[#111] border-2 border-white brutal-shadow relative overflow-hidden min-h-[400px] lg:min-h-0 group">
          {/* Faux Map Grid Pattern - Different color for driver */}
          <div className="absolute inset-0 opacity-20 pointer-events-none" 
               style={{ backgroundImage: 'linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000), linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000)', backgroundSize: '60px 60px', backgroundPosition: '0 0, 30px 30px' }}>
          </div>
          
          {/* Map Overlay UI */}
          <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
            <div className={`border-2 px-3 py-1 font-mono text-xs brutal-shadow-white pointer-events-auto transition-colors
              ${isOnline ? 'bg-black border-ridebid-green text-ridebid-green' : 'bg-black border-gray-600 text-gray-600'}`}>
              GPS_UPLINK :: {isOnline ? 'TRACKING' : 'DISCONNECTED'}
            </div>
            <div className="flex flex-col gap-2 pointer-events-auto">
              <button className="w-10 h-10 bg-white text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center text-xl hover:bg-gray-200">
                +
              </button>
              <button className="w-10 h-10 bg-white text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center text-xl hover:bg-gray-200">
                -
              </button>
              <button className="w-10 h-10 mt-4 bg-white text-black border-2 border-black font-bold brutal-shadow-hover flex items-center justify-center hover:bg-gray-200">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
                </svg>
              </button>
            </div>
          </div>

          {/* Central Map Marker (Driver Car) */}
          <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center transition-opacity duration-500 ${isOnline ? 'opacity-100' : 'opacity-50 grayscale'}`}>
            <div className="bg-white text-black font-bold text-xs px-2 py-1 border-2 border-black mb-1 whitespace-nowrap">
              YOUR CAB
            </div>
            {/* Car Icon representation */}
            <div className="w-6 h-10 bg-white border-2 border-black rounded-sm relative shadow-[0_0_15px_rgba(255,255,255,0.3)]">
              <div className="absolute top-1 left-1 right-1 h-2 bg-black opacity-80"></div>
              <div className="absolute bottom-2 left-1 right-1 h-2 bg-black opacity-80"></div>
              {isOnline && (
                <>
                  {/* Headlights */}
                  <div className="absolute -top-6 left-0 w-8 h-8 bg-yellow-400 blur-md opacity-40 rounded-full transform -translate-x-1/2"></div>
                  <div className="absolute -top-6 right-0 w-8 h-8 bg-yellow-400 blur-md opacity-40 rounded-full transform translate-x-1/2"></div>
                </>
              )}
            </div>
          </div>

          {/* Simulated active requests on map (if online) */}
          {isOnline && rideRequests.map(ride => (
            <div key={`map-${ride.id}`} className="absolute w-4 h-4 rounded-full bg-ridebid-green border-2 border-white shadow-[0_0_10px_#4f772d] animate-bounce cursor-pointer" 
                 style={{ 
                   top: `${30 + (ride.id * 15)}%`, 
                   left: `${20 + (ride.id * 20)}%` 
                 }}>
              <div className="absolute top-5 left-1/2 -translate-x-1/2 bg-black border border-ridebid-green text-white font-mono text-[10px] px-1 whitespace-nowrap">
                {ride.estFare}
              </div>
            </div>
          ))}

          {/* Offline Overlay */}
          {!isOnline && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-10 pointer-events-none"></div>
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
          background: #fff;
        }
      `}</style>
    </div>
  );
};

export default DriverDashboard;
