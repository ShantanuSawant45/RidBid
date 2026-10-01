import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapUpdater = ({ pickupCoords, dropoffCoords }) => {
  const map = useMap();
  
  React.useEffect(() => {
    if (pickupCoords && dropoffCoords) {
      const bounds = L.latLngBounds(
        [pickupCoords.lat, pickupCoords.lon],
        [dropoffCoords.lat, dropoffCoords.lon]
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (pickupCoords) {
      map.setView([pickupCoords.lat, pickupCoords.lon], 15);
    } else if (dropoffCoords) {
      map.setView([dropoffCoords.lat, dropoffCoords.lon], 15);
    }
  }, [pickupCoords, dropoffCoords, map]);

  return null;
};

const RiderDashboard = () => {
  const [pickup, setPickup] = useState('');
  const [dropoff, setDropoff] = useState('');
  const [vehicle, setVehicle] = useState('car');
  const [isSearching, setIsSearching] = useState(false);

  const [pickupCoords, SetPickupCoords] = useState(null)
  const [dropoffCoords, SetDropoffCoords] = useState(null)
  const [activeField, setActiveField] = useState(null)
  const [error, setError] = useState(null)
  const [activeRide, setActiveRide] = useState(null)
  const [suggestion, setSuggestion] = useState(null)



  const handleSearch = async (query, type) => {

    if (type === 'pickup') setPickup(query);
    else setDropoff(query);


    setActiveField(type);

    if (query.length < 3) {
      setSuggestion([])
      return
    }
    try {

      const res = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${query}&limit=5`);
      setSuggestion(res.data);
    } catch (err) {
      console.error("Error fetching locations", err);
    }
  };

  // this fucntion is called when the user clicks on any suggestion 

  const handleSelectLocation = (loc, type) => {

    if (type === 'pickup') {
      setPickup(loc.display_name);
      SetPickupCoords({ lat: parseFloat(loc.lat), lon: parseFloat(loc.lon) });
    }
    else {
      setDropoff(loc.display_name);
      SetDropoffCoords({ lat: parseFloat(loc.lat), lon: parseFloat(loc.lon) });
    }
    setSuggestion([]);
    setActiveField(null);

  };


  const handleRequestRide = async (e) => {
    e.preventDefault();
    setError('');

    if (!pickupCoords || !dropoffCoords) {
      setError('Please select locations from the dropdown suggestions');
      return;
    }

    setIsSearching(true);

    try {
      const token = localStorage.getItem('access_token');

      const payload = {
        pickup_latitude: pickupCoords.lat,
        pickup_longitude: pickupCoords.lon,
        pickup_address: pickup,
        dropoff_latitude: dropoffCoords.lat,
        dropoff_longitude: dropoffCoords.lon,
        dropoff_address: dropoff,
        vehicle_type: vehicle,
        number_of_passengers: 1
      };

      const response = await axios.post("http://localhost:8000/api/rides/", payload, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setIsSearching(false);
      setActiveRide(response.data.ride);
      setError(null);

    }
    catch (err) {
      setIsSearching(false);
      setError(err.response?.data?.error || err.response?.data?.non_field_errors?.[0] || 'Failed to create ride');
    }
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
                    onChange={(e) => handleSearch(e.target.value, 'pickup')}
                    onFocus={() => setActiveField('pickup')}
                    className="w-full bg-transparent border-2 border-gray-600 text-white p-3 pl-10 font-mono text-sm focus:outline-none focus:border-ridebid-green focus:bg-gray-900 transition-colors uppercase placeholder-gray-600"
                    required
                  />

                  {/* Suggestions */}
                  {activeField === 'pickup' && suggestion?.length > 0 && (
                    <div className="absolute left-0 right-0 mt-1 bg-black border-2 border-white max-h-48 overflow-y-auto z-20">
                      {suggestion.map((loc, idx) => (
                        <div
                          key={idx}
                          onClick={() => handleSelectLocation(loc, 'pickup')}
                          className="p-3 hover:bg-ridebid-green hover:text-black cursor-pointer border-b border-gray-600 last:border-0 flex flex-col"
                        >
                          <span className="font-bold text-sm">{loc.display_name}</span>
                          <span className="text-xs text-gray-400">{loc.type}</span>
                        </div>
                      ))}
                    </div>
                  )}


                  {/* Connecting Line */}
                  <div className="absolute left-[21px] top-[calc(100%-8px)] h-8 border-l-2 border-dashed border-gray-600 z-10"></div>
                </div>

                <div className="relative mt-2">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 w-3 h-3 bg-ridebid-green border-2 border-black"></div>
                  <input
                    type="text"
                    placeholder="ENTER DROP-OFF LOCATION"
                    value={dropoff}
                    onChange={(e) => handleSearch(e.target.value, 'dropoff')}
                    onFocus={() => setActiveField('dropoff')}
                    className="w-full bg-transparent border-2 border-gray-600 text-white p-3 pl-10 font-mono text-sm focus:outline-none focus:border-ridebid-green focus:bg-gray-900 transition-colors uppercase placeholder-gray-600"
                    required
                  />

                  {/* Suggestions */}
                  {activeField === 'dropoff' && suggestion?.length > 0 && (
                    <div className="absolute left-0 right-0 mt-1 bg-black border-2 border-white max-h-48 overflow-y-auto z-20">
                      {suggestion.map((loc, idx) => (
                        <div
                          key={idx}
                          onClick={() => handleSelectLocation(loc, 'dropoff')}
                          className="p-3 hover:bg-ridebid-green hover:text-black cursor-pointer border-b border-gray-600 last:border-0 flex flex-col"
                        >
                          <span className="font-bold text-sm">{loc.display_name}</span>
                          <span className="text-xs text-gray-400">{loc.type}</span>
                        </div>
                      ))}
                    </div>
                  )}


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
        <div className="flex-1 bg-[#111] border-2 border-white brutal-shadow relative z-0 min-h-[400px] lg:min-h-0">
          <MapContainer 
            center={[20.5937, 78.9629]} 
            zoom={5} 
            style={{ height: '100%', width: '100%', backgroundColor: '#111' }}
            zoomControl={false}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              className="map-tiles"
            />
            
            <MapUpdater pickupCoords={pickupCoords} dropoffCoords={dropoffCoords} />

            {pickupCoords && (
              <Marker position={[pickupCoords.lat, pickupCoords.lon]} />
            )}

            {dropoffCoords && (
              <Marker position={[dropoffCoords.lat, dropoffCoords.lon]} />
            )}

            {pickupCoords && dropoffCoords && (
              <Polyline 
                positions={[
                  [pickupCoords.lat, pickupCoords.lon],
                  [dropoffCoords.lat, dropoffCoords.lon]
                ]} 
                color="#4f772d" 
                weight={4}
                dashArray="10, 10"
              />
            )}
          </MapContainer>

          <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none z-[400]">
            <div className="bg-black border-2 border-white px-3 py-1 font-mono text-xs brutal-shadow-white pointer-events-auto">
              MAP_DATA_STREAM :: LIVE
            </div>
          </div>
          
          {isSearching && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[500]">
              <div className="bg-black border-2 border-ridebid-green p-8 max-w-sm w-full mx-4 text-center brutal-shadow pointer-events-auto">
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
        .map-tiles {
          filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
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
