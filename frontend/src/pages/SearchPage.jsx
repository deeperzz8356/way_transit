import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';

export default function SearchPage({ token, onBook }) {
  const [source, setSource] = useState('Mumbai');
  const [destination, setDestination] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedRoute, setSelectedRoute] = useState(null);

  const API_URL = 'http://localhost:8000';

  // Handle auto-redirect search from homepage
  useEffect(() => {
    if (window.searchDestination) {
      const dest = window.searchDestination;
      window.searchDestination = null; // Clear to prevent loops
      setDestination(dest);
      
      const autoSearch = async () => {
        setError('');
        setLoading(true);
        try {
          const response = await fetch(
            `${API_URL}/search/routes?source=Mumbai&destination=${encodeURIComponent(dest)}`,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || 'Search failed');
          }
          setResults(data);
          if (data.length > 0) {
            setSelectedRoute(data[0]); // default focus on first route
          }
        } catch (err) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      autoSearch();
    }
  }, [token]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setSelectedRoute(null);

    try {
      const response = await fetch(
        `${API_URL}/search/routes?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Search failed');
      }

      setResults(data);
      if (data.length > 0) {
        setSelectedRoute(data[0]); // default focus on first route
      }
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (route) => {
    setSelectedRoute(route);
  };

  return (
    <div className="search-container">
      <h2>Search Routes</h2>

      <div className="search-layout">
        <div className="search-controls">
          <form onSubmit={handleSearch} className="search-form">
            <input
              type="text"
              placeholder="Source (e.g., Mumbai)"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Destination (e.g., Pune)"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>

          {error && <div className="error">{error}</div>}

          {results.length > 0 && (
            <div className="results">
              <h3>Available Routes ({results.length})</h3>
              <p className="hint-text">Click a route card to view on map</p>
              <div className="results-list">
                {results.map((route) => {
                  const isSelected = selectedRoute && selectedRoute.id === route.id;
                  return (
                    <div 
                      key={route.id} 
                      className={`route-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleCardClick(route)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="route-header">
                        <span className="route-name">{route.source} → {route.destination}</span>
                        <span className="transport-badge" data-transport={route.transport.toLowerCase()}>
                          {route.transport.toUpperCase()}
                        </span>
                      </div>
                      <div className="route-details">
                        <p><strong>Departure:</strong> {route.departure_time}</p>
                        <p><strong>Arrival:</strong> {route.arrival_time}</p>
                        <p><strong>Duration:</strong> {calculateDuration(route.departure_time, route.arrival_time)}</p>
                      </div>
                      <div className="route-footer">
                        <span className="price">₹{route.price}</span>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation(); // prevent card selection trigger
                            onBook(route.id);
                          }} 
                          className="book-btn"
                        >
                          Book
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {results.length === 0 && !loading && !error && (
            <div className="no-results">Enter your route source and destination to view paths.</div>
          )}
        </div>

        {/* Route visualization map */}
        <div className="search-map-container">
          <MapComponent 
            source={selectedRoute ? selectedRoute.source : (results.length > 0 ? results[0].source : source)}
            destination={selectedRoute ? selectedRoute.destination : (results.length > 0 ? results[0].destination : destination)}
            transport={selectedRoute ? selectedRoute.transport : null}
            centerCity={source || 'mumbai'}
          />
        </div>
      </div>
    </div>
  );
}
