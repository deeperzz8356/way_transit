import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';

export default function HomePage({ token, onNavigate, onLogout }) {
  const [destination, setDestination] = useState('');
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    async function fetchBookings() {
      try {
        const response = await fetch(`${API_URL}/booking/my-bookings`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (response.ok) {
          // Sort by newest bookings
          setBookings(data.reverse());
        } else {
          setError(data.detail || 'Failed to load bookings');
        }
      } catch (err) {
        setError('Network error loading dashboard');
      } finally {
        setLoading(false);
      }
    }
    fetchBookings();
  }, [token]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (destination.trim()) {
      window.searchDestination = destination.trim();
      onNavigate('search');
    }
  };

  const nextTrip = () => {
    if (bookings.length > 1) {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % bookings.length);
    }
  };

  const prevTrip = () => {
    if (bookings.length > 1) {
      setCurrentIndex((prevIndex) => (prevIndex - 1 + bookings.length) % bookings.length);
    }
  };

  // Get active trip to display
  const activeBooking = bookings.length > 0 ? bookings[currentIndex] : null;

  // Helper to resolve transit icon
  const getTransitIcon = (transport) => {
    switch (transport?.toLowerCase()) {
      case 'flight': return '✈️';
      case 'train': return '🚂';
      case 'bus': return '🚌';
      case 'cab': return '🚗';
      default: return '🚌';
    }
  };

  return (
    <div className="home-page">
      {/* Header */}
      <div className="home-header">
        <div className="header-logo" onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>🚌 WAY</div>
        <div className="header-icons">
          <button className="icon-btn qr-btn" onClick={() => onNavigate('bookings')} title="My Bookings">🧭</button>
          <button className="icon-btn profile-btn" onClick={onLogout} title="Logout">🚪</button>
        </div>
      </div>

      {/* Map Section */}
      <div className="map-section">
        <div className="map-placeholder">
          {activeBooking ? (
            <MapComponent
              source={activeBooking.route.source}
              destination={activeBooking.route.destination}
              transport={activeBooking.route.transport}
            />
          ) : (
            <MapComponent centerCity="mumbai" />
          )}
        </div>

        {/* Location Badge */}
        <div className="location-badge">
          <span className="location-icon">📍</span>
          <span className="location-text">
            {activeBooking 
              ? `${activeBooking.route.source} → ${activeBooking.route.destination} (${activeBooking.route.transport})` 
              : 'Mumbai, India'}
          </span>
        </div>

        {/* Info Icon */}
        <button className="info-btn" onClick={() => alert("WAY Transit Interactive Map - Shows your active transit routes and ETA.")}>ℹ️</button>

        {/* Nearby Transits */}
        <div className="nearby-transits">
          <div className="transit-label">Transit Modes</div>
          <div className="transit-icons">
            <div className="transit-icon" title="Bus">🚌</div>
            <div className="transit-icon" title="Train">🚂</div>
            <div className="transit-icon" title="Flight">✈️</div>
            <div className="transit-icon" title="Cab">🚗</div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearchSubmit} className="search-bar-container">
        <div className="search-bar">
          <span className="search-icon">🔍</span>
          <input 
            type="text" 
            placeholder="Where To? (e.g. Pune)" 
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          />
          <button type="submit" style={{ display: 'none' }}></button>
          <button type="button" className="voice-btn" onClick={() => alert("Voice input not supported in MVP")}>🎤</button>
        </div>
        <button type="submit" className="notification-btn" title="Search">🔔</button>
      </form>

      {/* Bottom Cards Section */}
      <div className="cards-grid">
        {/* Upcoming Trips Card */}
        <div className="card upcoming-card">
          <div className="card-header">
            <span className="card-title">
              {bookings.length > 0 
                ? `Upcoming Trips (${currentIndex + 1} of ${bookings.length})` 
                : 'No Upcoming Trips'}
            </span>
            {bookings.length > 1 && (
              <div className="nav-arrows">
                <button className="arrow left" onClick={prevTrip}>‹</button>
                <button className="arrow right" onClick={nextTrip}>›</button>
              </div>
            )}
          </div>
        </div>

        {/* Trip Details Card - Left */}
        {activeBooking ? (
          <div className="card trip-details-card" onClick={() => onNavigate('bookings')} style={{ cursor: 'pointer' }}>
            <div className="ticket-badge">Tickets Booked</div>
            
            <div className="trip-info">
              <div className="temperature">☀️ 28°C &bull; {calculateDuration(activeBooking.route.departure_time, activeBooking.route.arrival_time)}</div>
              <div className="transit-row">
                <div className="transit-icon-small">{getTransitIcon(activeBooking.route.transport)}</div>
              </div>
            </div>

            <div className="trip-time">
              <div className="trip-route">{activeBooking.route.source} → {activeBooking.route.destination}</div>
              <div className="trip-time-text">{activeBooking.route.departure_time} - {activeBooking.route.arrival_time}</div>
            </div>
          </div>
        ) : (
          <div className="card trip-details-card" onClick={() => onNavigate('search')} style={{ cursor: 'pointer' }}>
            <div className="ticket-badge" style={{ backgroundColor: '#7f8c8d' }}>No Bookings</div>
            
            <div className="trip-info">
              <div className="temperature">Ready to travel?</div>
            </div>

            <div className="trip-time">
              <div className="trip-route">Where to next?</div>
              <div className="trip-time-text">Find routes and book a ride</div>
            </div>
          </div>
        )}

        {/* Plan a Trip Card - Right */}
        <div className="card plan-trip-card" onClick={() => onNavigate('search')} style={{ cursor: 'pointer' }}>
          <div className="plan-trip-content">
            <div className="plan-trip-text">
              <div className="plan-label">Plan a trip</div>
              <div className="plan-tagline">Find Your Way</div>
            </div>
            <div className="plan-trip-number">{bookings.length}</div>
          </div>
        </div>

        {/* Quick Actions - Bottom Left */}
        <div className="quick-actions-row">
          <button className="quick-action-btn" onClick={() => onNavigate('bookings')} title="Bookings">
            <div className="action-icon">👥</div>
          </button>
          <button className="quick-action-btn with-badge" onClick={() => onNavigate('search')} title="Search">
            <div className="action-icon">🧭</div>
            <div className="badge">5</div>
          </button>
        </div>
      </div>

      {/* Promo Card */}
      <div className="promo-card">
        <div className="promo-content">
          <div className="promo-text">
            <div className="promo-title">Get discounts, perks & other benefits</div>
            <div className="promo-subtitle">on purchases with way credits</div>
          </div>
          <div className="promo-time">→ 08:32 - ← 14:32</div>
        </div>
      </div>
    </div>
  );
}
