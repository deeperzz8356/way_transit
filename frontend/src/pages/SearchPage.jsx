import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';
import './SearchPage.css';

const API_BASE = 'http://localhost:8000'; // Make sure this matches your backend

export default function SearchPage({ token, onBook }) {
  const [source, setSource] = useState('Versova');
  const [destination, setDestination] = useState('Ghatkopar');
  
  const [routes, setRoutes] = useState([]);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);

  // 1. Fetch available routes based on source and destination
  useEffect(() => {
    async function fetchRoutes() {
      if (!source || !destination) return;
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/search/routes?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}`);
        const data = await res.json();
        setRoutes(data);
        if (data.length > 0) {
          setSelectedRouteId(data[0].id); // Auto-select first route
        } else {
          setRouteData(null);
        }
      } catch (err) {
        console.error("Failed to fetch routes:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchRoutes();
  }, [source, destination]);

  // 2. Fetch the path (stops/coordinates) for the selected route
  useEffect(() => {
    async function fetchRoutePath() {
      if (!selectedRouteId) return;
      try {
        const res = await fetch(`${API_BASE}/search/route/${selectedRouteId}/path`);
        const data = await res.json();
        setRouteData(data);
      } catch (err) {
        console.error("Failed to fetch route path:", err);
      }
    }
    fetchRoutePath();
  }, [selectedRouteId]);

  return (
    <div className="search-page-wrapper">
      <div className="map-background">
        <MapComponent routeData={routeData} />
      </div>
      
      <TopOverlay 
        source={source} 
        destination={destination}
        onSourceChange={setSource}
        onDestChange={setDestination}
      />
      
      <BottomSheet 
        routes={routes} 
        loading={loading}
        selectedRouteId={selectedRouteId}
        onSelectRoute={setSelectedRouteId}
        onBook={onBook} 
      />
    </div>
  );
}

function TopOverlay({ source, destination, onSourceChange, onDestChange }) {
  return (
    <div className="search-overlay-top">
      <div className="route-header-card">
        <div className="route-endpoints">
          <div className="endpoint source">
            <input 
              type="text" 
              value={source} 
              onChange={e => onSourceChange(e.target.value)} 
              className="ep-name-input"
              placeholder="Source"
            />
          </div>
          <div className="route-distance">
            <div className="distance-badge">To</div>
          </div>
          <div className="endpoint dest">
            <input 
              type="text" 
              value={destination} 
              onChange={e => onDestChange(e.target.value)} 
              className="ep-name-input"
              placeholder="Destination"
            />
          </div>
        </div>
        <TransportModes />
      </div>
    </div>
  );
}

function TransportModes() {
  return (
    <div className="transport-modes">
      <button className="mode-btn active">🚇 All</button>
      <button className="mode-btn">🚌 Bus</button>
      <button className="mode-btn">🚝 Metro</button>
    </div>
  );
}

function BottomSheet({ routes, loading, selectedRouteId, onSelectRoute, onBook }) {
  return (
    <div className="search-bottom-sheet">
      <div className="sheet-handle"></div>
      <div className="journey-list">
        {loading && <div style={{padding: '20px', textAlign: 'center'}}>Finding routes...</div>}
        
        {!loading && routes.length === 0 && (
          <div style={{padding: '20px', textAlign: 'center'}}>No routes found between these stops.</div>
        )}

        {!loading && routes.map(r => (
          <JourneyCard 
            key={r.id} 
            route={r} 
            isSelected={r.id === selectedRouteId}
            onSelect={() => onSelectRoute(r.id)}
            onBook={() => onBook(r.id)} 
          />
        ))}
      </div>
    </div>
  );
}

function JourneyCard({ route, isSelected, onSelect, onBook }) {
  const icon = route.mode === 'metro' ? '🚝' : '🚌';
  const timeStr = `${route.departure_time} - ${route.arrival_time}`;
  
  return (
    <div 
      className={`journey-card ${isSelected ? 'selected' : ''}`} 
      onClick={onSelect}
      style={isSelected ? { border: '2px solid #007bff' } : {}}
    >
      <div className="journey-icon">{icon}</div>
      <div className="journey-info">
        <h4>{route.name}</h4>
        <div className="journey-time">
          <span>🕒 {timeStr}</span>
        </div>
      </div>
      <div className="journey-price">₹{route.price}</div>
      <button 
        className="go-btn" 
        onClick={(e) => {
          e.stopPropagation();
          onBook();
        }}
      >→</button>
    </div>
  );
}
