import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';

export default function BookingPage({ token, routeId, onSuccess, onCancel }) {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bookingInProgress, setBookingInProgress] = useState(false);
  const [error, setError] = useState('');

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    async function fetchRouteDetails() {
      if (!routeId) {
        setError('No route selected');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/search/route/${routeId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        if (response.ok) {
          setRoute(data);
        } else {
          setError(data.detail || 'Failed to load route details');
        }
      } catch (err) {
        setError('Network error fetching route details');
      } finally {
        setLoading(false);
      }
    }
    fetchRouteDetails();
  }, [routeId, token]);

  const handleConfirmBooking = async () => {
    setError('');
    setBookingInProgress(true);

    try {
      const response = await fetch(`${API_URL}/booking/book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ route_id: routeId })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Booking failed');
      }

      alert('✓ Booking confirmed successfully!');
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setBookingInProgress(false);
    }
  };

  const getTransitIcon = (transport) => {
    switch (transport?.toLowerCase()) {
      case 'flight': return '✈️';
      case 'train': return '🚂';
      case 'bus': return '🚌';
      case 'cab': return '🚗';
      default: return '🚌';
    }
  };

  if (loading) {
    return <div className="loading">Loading booking details...</div>;
  }

  if (error && !route) {
    return (
      <div className="booking-container">
        <h2>Confirm Booking</h2>
        <div className="error">{error}</div>
        <button onClick={onCancel} className="confirm-btn" style={{ backgroundColor: '#7f8c8d' }}>
          Back to Search
        </button>
      </div>
    );
  }

  return (
    <div className="booking-container confirmation-page">
      <h2>Confirm Booking</h2>

      {error && <div className="error">{error}</div>}

      <div className="booking-layout">
        <div className="booking-details-panel">
          <div className="booking-card summary-card">
            <div className="route-header">
              <span className="route-name">{route.source} → {route.destination}</span>
              <span className="transport-badge" data-transport={route.transport.toLowerCase()}>
                {getTransitIcon(route.transport)} {route.transport.toUpperCase()}
              </span>
            </div>

            <div className="booking-info-list">
              <div className="info-item">
                <span className="info-label">Departure</span>
                <span className="info-value">{route.departure_time}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Arrival</span>
                <span className="info-value">{route.arrival_time}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Duration</span>
                <span className="info-value">{calculateDuration(route.departure_time, route.arrival_time)}</span>
              </div>
              <div className="info-item price-item">
                <span className="info-label">Total Price</span>
                <span className="info-value price-text">₹{route.price}</span>
              </div>
            </div>

            <div className="booking-actions">
              <button
                onClick={handleConfirmBooking}
                disabled={bookingInProgress}
                className="confirm-btn"
              >
                {bookingInProgress ? 'Processing...' : 'Confirm Booking'}
              </button>
              
              <button
                onClick={onCancel}
                disabled={bookingInProgress}
                className="cancel-btn"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>

        {/* Interactive map visualization */}
        <div className="booking-map-panel">
          <MapComponent 
            source={route.source}
            destination={route.destination}
            transport={route.transport}
            centerCity={route.source}
          />
        </div>
      </div>
    </div>
  );
}
