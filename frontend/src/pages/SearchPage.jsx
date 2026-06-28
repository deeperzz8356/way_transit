import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';
import './SearchPage.css'; // force reload

export default function SearchPage({ token, onBook }) {
  const [source, setSource] = useState('Mahavir CHS');
  const [destination, setDestination] = useState('Atlas Skilltech University');

  return (
    <div className="search-page-wrapper">
      <div className="map-background">
        <MapComponent useDefaultStyle={true} />
      </div>
      <TopOverlay source={source} destination={destination} />
      <BottomSheet onBook={onBook} />
    </div>
  );
}

function TopOverlay({ source, destination }) {
  return (
    <div className="search-overlay-top">
      <div className="route-header-card">
        <div className="route-endpoints">
          <div className="endpoint source">
            <span className="ep-code">MHV</span>
            <span className="ep-name">{source}</span>
          </div>
          <div className="route-distance">
            <div className="distance-badge">15km</div>
          </div>
          <div className="endpoint dest">
            <span className="ep-code">ATLAS</span>
            <span className="ep-name">{destination}</span>
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
      <button className="mode-btn active">🚌</button>
      <button className="mode-btn">🚆</button>
      <button className="mode-btn">🚝</button>
    </div>
  );
}

function BottomSheet({ onBook }) {
  const journeys = [
    { id: 1, title: 'Fastest Journey', price: '35', time: '15 min' },
    { id: 2, title: 'Comfort Journey', price: '65', time: '15 min' },
    { id: 3, title: 'Budget Journey', price: '30', time: '15 min' },
    { id: 4, title: 'Walk Assisted Journey', price: '35', time: '15 min' },
    { id: 5, title: 'Shortest Journey', price: '35', time: '15 min' }
  ];

  return (
    <div className="search-bottom-sheet">
      <div className="sheet-handle"></div>
      <div className="journey-list">
        {journeys.map(j => (
          <JourneyCard key={j.id} journey={j} onBook={() => onBook(j.id)} />
        ))}
      </div>
    </div>
  );
}

function JourneyCard({ journey, onBook }) {
  return (
    <div className="journey-card" onClick={onBook}>
      <div className="journey-icon">🚝</div>
      <div className="journey-info">
        <h4>{journey.title}</h4>
        <div className="journey-time">
          <span>🕒 {journey.time}</span>
          <span className="transfer-dots">
            <span className="dot bus"></span>
            <span className="dot train"></span>
          </span>
        </div>
      </div>
      <div className="journey-price">₹{journey.price}</div>
      <button className="go-btn">→</button>
    </div>
  );
}
