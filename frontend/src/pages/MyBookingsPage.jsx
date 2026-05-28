import React, { useEffect, useState } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';

export default function MyBookingsPage({ token }) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedBooking, setSelectedBooking] = useState(null);

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const response = await fetch(`${API_URL}/booking/my-bookings`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || 'Failed to load bookings');
        }

        // Sort bookings by creation date descending
        const sortedBookings = data.reverse();
        setBookings(sortedBookings);
        if (sortedBookings.length > 0) {
          setSelectedBooking(sortedBookings[0]); // default to first booking
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, [token]);

  const handleCardClick = (booking) => {
    setSelectedBooking(booking);
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

  if (loading) return <div className="loading">Loading bookings...</div>;

  return (
    <div className="bookings-container">
      <h2>My Bookings</h2>

      {error && <div className="error">{error}</div>}

      {bookings.length > 0 ? (
        <div className="bookings-layout">
          <div className="bookings-controls">
            <p className="hint-text">Select a booking to view its route path</p>
            <div className="bookings-list">
              {bookings.map((booking) => {
                const isSelected = selectedBooking && selectedBooking.id === booking.id;
                return (
                  <div 
                    key={booking.id} 
                    className={`booking-card clickable ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleCardClick(booking)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="booking-header">
                      <h3>{booking.route.source} → {booking.route.destination}</h3>
                      <span className={`status ${booking.status.toLowerCase()}`}>
                        {booking.status}
                      </span>
                    </div>
                    <div className="booking-details">
                      <p>
                        <strong>Transport:</strong> 
                        <span style={{ marginLeft: '4px' }}>
                          {getTransitIcon(booking.route.transport)} {booking.route.transport.toUpperCase()}
                        </span>
                      </p>
                      <p><strong>Departure:</strong> {booking.route.departure_time}</p>
                      <p><strong>Arrival:</strong> {booking.route.arrival_time}</p>
                      <p><strong>Duration:</strong> {calculateDuration(booking.route.departure_time, booking.route.arrival_time)}</p>
                      <p><strong>Price:</strong> ₹{booking.route.price}</p>
                      <p><strong>Booked on:</strong> {new Date(booking.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Booking Map View */}
          <div className="bookings-map-container">
            {selectedBooking && (
              <MapComponent 
                source={selectedBooking.route.source}
                destination={selectedBooking.route.destination}
                transport={selectedBooking.route.transport}
                centerCity={selectedBooking.route.source}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="no-bookings">No bookings yet. Search and book a route to get started!</div>
      )}
    </div>
  );
}
