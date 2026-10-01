import React, { useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// ─── Leaflet default icon fix for bundlers ────────────────────────────────────
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000';

const VEHICLE_OPTIONS = [
  { id: 'bike', label: 'MOTO', icon: '🏍️', price: '₹50 - ₹70', time: '2 min' },
  { id: 'auto', label: 'AUTO', icon: '🛺', price: '₹80 - ₹110', time: '4 min' },
  { id: 'car',  label: 'CAB',  icon: '🚗', price: '₹150 - ₹200', time: '5 min' },
];

const STATUS_CONFIG = {
  requested:   { label: 'BROADCAST', color: 'text-yellow-400', border: 'border-yellow-400', bg: 'bg-yellow-400/10', dot: 'bg-yellow-400', desc: 'Broadcasting your request to nearby drivers…' },
  bidding:     { label: 'BIDDING',   color: 'text-ridebid-green', border: 'border-ridebid-green', bg: 'bg-ridebid-green/10', dot: 'bg-ridebid-green', desc: 'Drivers are placing bids. Review them below.' },
  accepted:    { label: 'ACCEPTED',  color: 'text-blue-400',   border: 'border-blue-400', bg: 'bg-blue-400/10', dot: 'bg-blue-400', desc: 'A driver has been assigned. They are on the way!' },
  in_progress: { label: 'IN PROGRESS', color: 'text-purple-400', border: 'border-purple-400', bg: 'bg-purple-400/10', dot: 'bg-purple-400', desc: 'Your ride is in progress.' },
  completed:   { label: 'COMPLETED', color: 'text-green-400',  border: 'border-green-400', bg: 'bg-green-400/10', dot: 'bg-green-400', desc: 'Your ride is complete. Thank you!' },
  cancelled:   { label: 'CANCELLED', color: 'text-red-400',    border: 'border-red-400', bg: 'bg-red-400/10', dot: 'bg-red-400', desc: 'This ride was cancelled.' },
};

// ─── Map auto-zoom helper ─────────────────────────────────────────────────────
const MapUpdater = ({ pickupCoords, dropoffCoords }) => {
  const map = useMap();
  React.useEffect(() => {
    if (pickupCoords && dropoffCoords) {
      const bounds = L.latLngBounds(
        [pickupCoords.lat, pickupCoords.lon],
        [dropoffCoords.lat, dropoffCoords.lon]
      );
      map.fitBounds(bounds, { padding: [60, 60] });
    } else if (pickupCoords) {
      map.setView([pickupCoords.lat, pickupCoords.lon], 15);
    } else if (dropoffCoords) {
      map.setView([dropoffCoords.lat, dropoffCoords.lon], 15);
    }
  }, [pickupCoords, dropoffCoords, map]);
  return null;
};

// ─── Active Ride Status Board ─────────────────────────────────────────────────
const ActiveRideBoard = ({ ride, onCancel, isCancelling, cancelError }) => {
  const cfg = STATUS_CONFIG[ride.status] || STATUS_CONFIG.requested;
  const canCancel = ['requested', 'bidding', 'accepted'].includes(ride.status);

  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      {/* Header */}
      <div className="bg-black border-2 border-white brutal-shadow">
        <div className="bg-white p-2 border-b-2 border-white flex justify-between items-center">
          <span className="text-black font-mono text-xs font-bold uppercase tracking-widest">
            ride_status.exe
          </span>
          <div className="flex gap-1">
            <div className="w-3 h-3 border-2 border-black bg-black"></div>
            <div className="w-3 h-3 border-2 border-black bg-ridebid-green"></div>
          </div>
        </div>

        <div className="p-6">
          {/* Status Badge */}
          <div className={`flex items-center gap-3 p-3 border-2 ${cfg.border} ${cfg.bg} mb-6`}>
            <span className={`w-2.5 h-2.5 rounded-full ${cfg.dot} animate-pulse flex-shrink-0`}></span>
            <div>
              <div className={`font-mono text-xs font-bold tracking-widest ${cfg.color}`}>STATUS: {cfg.label}</div>
              <div className="font-mono text-xs text-gray-400 mt-0.5">{cfg.desc}</div>
            </div>
          </div>

          {/* Ride ID */}
          <div className="font-mono text-xs text-gray-500 mb-4 tracking-widest">RIDE_ID: #{String(ride.id).padStart(6, '0')}</div>

          {/* Route Info */}
          <div className="flex flex-col gap-2 mb-6">
            <div className="flex items-start gap-3 p-3 border border-gray-800 bg-gray-900/50">
              <div className="w-3 h-3 bg-white border-2 border-black flex-shrink-0 mt-0.5"></div>
              <div>
                <div className="font-mono text-[10px] text-gray-500 tracking-widest">PICKUP</div>
                <div className="font-mono text-xs text-white mt-0.5 line-clamp-2">{ride.pickup_address}</div>
              </div>
            </div>
            <div className="ml-[9px] border-l-2 border-dashed border-gray-700 h-4"></div>
            <div className="flex items-start gap-3 p-3 border border-gray-800 bg-gray-900/50">
              <div className="w-3 h-3 bg-ridebid-green border-2 border-black flex-shrink-0 mt-0.5"></div>
              <div>
                <div className="font-mono text-[10px] text-gray-500 tracking-widest">DROP-OFF</div>
                <div className="font-mono text-xs text-white mt-0.5 line-clamp-2">{ride.dropoff_address}</div>
              </div>
            </div>
          </div>

          {/* Vehicle & Passengers */}
          <div className="flex gap-3 mb-6">
            <div className="flex-1 p-3 border border-gray-800 bg-gray-900/50">
              <div className="font-mono text-[10px] text-gray-500 tracking-widest">VEHICLE</div>
              <div className="font-mono text-sm text-white font-bold uppercase mt-1">{ride.vehicle_type || '—'}</div>
            </div>
            <div className="flex-1 p-3 border border-gray-800 bg-gray-900/50">
              <div className="font-mono text-[10px] text-gray-500 tracking-widest">PASSENGERS</div>
              <div className="font-mono text-sm text-white font-bold mt-1">{ride.number_of_passengers}</div>
            </div>
          </div>

          {/* Cancel Error */}
          {cancelError && (
            <div className="mb-4 bg-red-900/40 border border-red-500 text-red-300 p-3 font-mono text-xs">
              ERR: {cancelError}
            </div>
          )}

          {/* Cancel Button */}
          {canCancel ? (
            <button
              onClick={onCancel}
              disabled={isCancelling}
              className="w-full border-2 border-red-500 text-red-400 font-mono text-sm font-bold uppercase tracking-widest py-3 hover:bg-red-500 hover:text-black transition-all disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
            >
              {isCancelling ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></span>
                  CANCELLING…
                </span>
              ) : 'CANCEL RIDE'}
            </button>
          ) : (
            <div className="text-center font-mono text-xs text-gray-600 py-3 border border-gray-800">
              RIDE CANNOT BE CANCELLED AT THIS STAGE
            </div>
          )}
        </div>
      </div>

      {/* Bids placeholder — will become live in Phase 3 */}
      {(ride.status === 'requested' || ride.status === 'bidding') && (
        <div className="bg-black border-2 border-gray-800 p-4">
          <h3 className="font-mono text-xs font-bold text-gray-400 mb-3 tracking-widest">INCOMING BIDS</h3>
          <div className="border border-dashed border-gray-700 p-6 text-center">
            <div className="w-8 h-8 border-2 border-gray-700 border-t-ridebid-green rounded-full animate-spin mx-auto mb-3"></div>
            <p className="font-mono text-xs text-gray-500">AWAITING DRIVER BIDS…</p>
            <p className="font-mono text-[10px] text-gray-700 mt-1">Real-time bids will appear here</p>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Location Autocomplete Input ──────────────────────────────────────────────
const LocationInput = ({ label, value, placeholder, dot, onSearch, suggestions, isActive, onSelect, onFocus }) => (
  <div className="relative">
    <div className={`absolute left-4 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-black ${dot}`}></div>
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onSearch(e.target.value)}
      onFocus={onFocus}
      className="w-full bg-transparent border-2 border-gray-600 text-white p-3 pl-10 font-mono text-sm focus:outline-none focus:border-ridebid-green focus:bg-gray-900 transition-colors uppercase placeholder-gray-600"
      autoComplete="off"
      required
    />
    {isActive && suggestions?.length > 0 && (
      <div className="absolute left-0 right-0 top-full mt-1 bg-black border-2 border-white max-h-48 overflow-y-auto z-[600] shadow-2xl">
        {suggestions.map((loc, idx) => (
          <div
            key={idx}
            onMouseDown={(e) => { e.preventDefault(); onSelect(loc); }}
            className="p-3 hover:bg-ridebid-green hover:text-black cursor-pointer border-b border-gray-800 last:border-0 flex flex-col transition-colors"
          >
            <span className="font-mono text-xs font-bold leading-tight">{loc.display_name.split(',')[0]}</span>
            <span className="font-mono text-[10px] text-gray-400 hover:text-black/70 truncate mt-0.5">{loc.display_name}</span>
          </div>
        ))}
      </div>
    )}
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────
const RiderDashboard = () => {
  // ── Form state ──────────────────────────────────────────────────────────────
  const [pickup, setPickup]             = useState('');
  const [dropoff, setDropoff]           = useState('');
  const [vehicle, setVehicle]           = useState('car');
  const [pickupCoords, setPickupCoords] = useState(null);
  const [dropoffCoords, setDropoffCoords] = useState(null);
  const [suggestions, setSuggestions]   = useState([]);
  const [activeField, setActiveField]   = useState(null);
  const [formError, setFormError]       = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ── Active ride state ────────────────────────────────────────────────────────
  const [activeRide, setActiveRide]         = useState(null);
  const [isCancelling, setIsCancelling]     = useState(false);
  const [cancelError, setCancelError]       = useState('');

  // ── Debounce ref for geocoding ───────────────────────────────────────────────
  const searchTimer = useRef(null);

  // ── Geocoding (autocomplete) ─────────────────────────────────────────────────
  const handleSearch = useCallback((query, type) => {
    if (type === 'pickup') { setPickup(query); setPickupCoords(null); }
    else                   { setDropoff(query); setDropoffCoords(null); }
    setActiveField(type);
    setFormError('');

    clearTimeout(searchTimer.current);
    if (query.length < 3) { setSuggestions([]); return; }

    searchTimer.current = setTimeout(async () => {
      try {
        const res = await axios.get(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=6&addressdetails=1`,
          { headers: { 'Accept-Language': 'en' } }
        );
        setSuggestions(res.data);
      } catch {
        // Silently fail — autocomplete is non-critical
      }
    }, 300);
  }, []);

  const handleSelectLocation = useCallback((loc, type) => {
    const coords = { lat: parseFloat(loc.lat), lon: parseFloat(loc.lon) };
    if (type === 'pickup') { setPickup(loc.display_name); setPickupCoords(coords); }
    else                   { setDropoff(loc.display_name); setDropoffCoords(coords); }
    setSuggestions([]);
    setActiveField(null);
  }, []);

  // ── Submit ride request ──────────────────────────────────────────────────────
  const handleRequestRide = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!pickupCoords || !dropoffCoords) {
      setFormError('Please select both locations from the dropdown list.');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const { data } = await axios.post(
        `${API_BASE}/api/rides/`,
        {
          pickup_latitude:      pickupCoords.lat,
          pickup_longitude:     pickupCoords.lon,
          pickup_address:       pickup,
          dropoff_latitude:     dropoffCoords.lat,
          dropoff_longitude:    dropoffCoords.lon,
          dropoff_address:      dropoff,
          vehicle_type:         vehicle,
          number_of_passengers: 1,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setActiveRide(data.ride);
    } catch (err) {
      const errData = err.response?.data;
      setFormError(
        errData?.error ||
        errData?.non_field_errors?.[0] ||
        Object.values(errData || {})[0]?.[0] ||
        'Failed to create ride. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Cancel ride ──────────────────────────────────────────────────────────────
  const handleCancelRide = async () => {
    if (!activeRide) return;
    setCancelError('');
    setIsCancelling(true);
    try {
      const token = localStorage.getItem('access_token');
      const { data } = await axios.post(
        `${API_BASE}/api/rides/${activeRide.id}/cancel/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Update with cancelled ride from backend
      setActiveRide(data.ride);
    } catch (err) {
      setCancelError(
        err.response?.data?.error || 'Could not cancel the ride. Please try again.'
      );
    } finally {
      setIsCancelling(false);
    }
  };

  // ── Book new ride (reset all state) ─────────────────────────────────────────
  const handleBookNew = () => {
    setActiveRide(null);
    setPickup('');
    setDropoff('');
    setPickupCoords(null);
    setDropoffCoords(null);
    setVehicle('car');
    setFormError('');
    setCancelError('');
  };

  // ── Left panel content ───────────────────────────────────────────────────────
  const renderLeftPanel = () => {
    if (activeRide) {
      return (
        <>
          {/* Book new ride link — only when ride is cancelled or completed */}
          {(activeRide.status === 'cancelled' || activeRide.status === 'completed') && (
            <button
              onClick={handleBookNew}
              className="w-full bg-ridebid-green text-black font-mono font-bold uppercase tracking-widest py-3 brutal-shadow-white hover:brightness-110 transition-all border-2 border-transparent hover:border-white"
            >
              + BOOK NEW RIDE
            </button>
          )}
          <ActiveRideBoard
            ride={activeRide}
            onCancel={handleCancelRide}
            isCancelling={isCancelling}
            cancelError={cancelError}
          />
        </>
      );
    }

    return (
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
          <h2 className="text-2xl font-extrabold uppercase mb-6 tracking-tight">WHERE TO?</h2>

          {formError && (
            <div className="mb-5 bg-red-900/40 border-2 border-red-500 text-red-300 p-3 font-mono text-xs animate-fade-in">
              ERR: {formError}
            </div>
          )}

          <form onSubmit={handleRequestRide} className="flex flex-col gap-5">
            {/* Pickup */}
            <div>
              <LocationInput
                label="PICKUP"
                value={pickup}
                placeholder="ENTER PICKUP LOCATION"
                dot="bg-white"
                onSearch={(q) => handleSearch(q, 'pickup')}
                suggestions={suggestions}
                isActive={activeField === 'pickup'}
                onSelect={(loc) => handleSelectLocation(loc, 'pickup')}
                onFocus={() => setActiveField('pickup')}
              />
              <div className="ml-[21px] border-l-2 border-dashed border-gray-700 h-6"></div>
            </div>

            {/* Dropoff */}
            <LocationInput
              label="DROP-OFF"
              value={dropoff}
              placeholder="ENTER DROP-OFF LOCATION"
              dot="bg-ridebid-green"
              onSearch={(q) => handleSearch(q, 'dropoff')}
              suggestions={suggestions}
              isActive={activeField === 'dropoff'}
              onSelect={(loc) => handleSelectLocation(loc, 'dropoff')}
              onFocus={() => setActiveField('dropoff')}
            />

            {/* Vehicle + submit — only when both have confirmed coords */}
            {pickupCoords && dropoffCoords && (
              <div className="mt-4 animate-fade-in">
                <h3 className="font-mono text-xs font-bold text-gray-400 mb-3 tracking-widest">SELECT VEHICLE</h3>
                <div className="flex flex-col gap-3">
                  {VEHICLE_OPTIONS.map((opt) => (
                    <div
                      key={opt.id}
                      onClick={() => setVehicle(opt.id)}
                      className={`border-2 p-3 flex items-center justify-between cursor-pointer transition-all ${
                        vehicle === opt.id
                          ? 'border-ridebid-green bg-gray-900 brutal-shadow'
                          : 'border-gray-800 hover:border-gray-600 bg-black'
                      }`}
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

                <div className="mt-5 p-4 bg-gray-900 border-2 border-ridebid-green border-dashed">
                  <div className="flex justify-between items-center font-mono text-sm mb-1">
                    <span className="text-gray-400">ESTIMATED FARE</span>
                    <span className="font-bold text-ridebid-green">
                      {VEHICLE_OPTIONS.find((v) => v.id === vehicle)?.price}
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-500 font-mono">Final price determined by driver bidding.</p>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-5 bg-ridebid-green text-black font-bold uppercase tracking-widest px-6 py-4 brutal-shadow-white transition-all border-2 border-transparent hover:border-white font-mono disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
                >
                  <span className="relative z-10">
                    {isSubmitting ? 'BROADCASTING…' : 'REQUEST RIDE'}
                  </span>
                  {isSubmitting && (
                    <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                  )}
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    );
  };

  // ── Map coords ───────────────────────────────────────────────────────────────
  const mapPickup  = activeRide
    ? { lat: activeRide.pickup_coords?.latitude,  lon: activeRide.pickup_coords?.longitude }
    : pickupCoords;
  const mapDropoff = activeRide
    ? { lat: activeRide.dropoff_coords?.latitude, lon: activeRide.dropoff_coords?.longitude }
    : dropoffCoords;

  return (
    <div className="min-h-screen bg-ridebid-black flex flex-col font-sans selection:bg-ridebid-green selection:text-black text-white">
      {/* Grid background */}
      <div
        className="fixed inset-0 opacity-10 pointer-events-none"
        style={{ backgroundImage: 'linear-gradient(#4f772d 1px, transparent 1px), linear-gradient(90deg, #4f772d 1px, transparent 1px)', backgroundSize: '40px 40px' }}
      />

      {/* Navbar */}
      <header className="relative z-20 bg-black border-b-2 border-white p-4 flex justify-between items-center brutal-shadow-white sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-ridebid-green flex items-center justify-center font-bold text-black transform -skew-x-12">RB</div>
          <span className="text-xl font-bold tracking-widest text-white uppercase">RIDEBID / RIDER</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 border-2 border-ridebid-green px-3 py-1 font-mono text-xs">
            <span className="w-2 h-2 bg-ridebid-green rounded-full animate-pulse"></span>
            NETWORK ONLINE
          </div>
          <Link
            to="/"
            className="bg-white text-black font-bold uppercase tracking-widest px-4 py-1 brutal-shadow-hover transition-all border-2 border-transparent hover:border-black font-mono text-sm"
          >
            LOGOUT
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col lg:flex-row relative z-10 p-4 lg:p-6 gap-6 lg:h-[calc(100vh-76px)]">

        {/* Left Panel */}
        <div className="w-full lg:w-[420px] flex flex-col gap-4 lg:h-full lg:overflow-y-auto pb-6 custom-scrollbar">
          {renderLeftPanel()}
        </div>

        {/* Right: Map */}
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
            <MapUpdater pickupCoords={mapPickup} dropoffCoords={mapDropoff} />

            {mapPickup?.lat && <Marker position={[mapPickup.lat, mapPickup.lon]} />}
            {mapDropoff?.lat && <Marker position={[mapDropoff.lat, mapDropoff.lon]} />}
            {mapPickup?.lat && mapDropoff?.lat && (
              <Polyline
                positions={[[mapPickup.lat, mapPickup.lon], [mapDropoff.lat, mapDropoff.lon]]}
                color="#4f772d"
                weight={4}
                dashArray="10, 10"
              />
            )}
          </MapContainer>

          {/* Map HUD */}
          <div className="absolute top-4 left-4 pointer-events-none z-[400]">
            <div className="bg-black border-2 border-white px-3 py-1 font-mono text-xs brutal-shadow-white">
              MAP_DATA_STREAM :: LIVE
            </div>
          </div>
        </div>
      </main>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #000; border-left: 1px solid #222; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #4f772d; }
        .map-tiles { filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }
        .animate-fade-in { animation: fadeIn 0.25s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      `}</style>
    </div>
  );
};

export default RiderDashboard;
