import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix leaflet default icon issues
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow, iconAnchor: [12, 41] });
L.Marker.prototype.options.icon = DefaultIcon;

// Custom Icons
const busIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  iconSize: [25, 41], iconAnchor: [12, 41]
});

const metroIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  iconSize: [25, 41], iconAnchor: [12, 41]
});

const blueDotIcon = new L.DivIcon({
  className: 'blue-pulsing-dot',
  html: '<div style="width: 15px; height: 15px; background: #007bff; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #007bff;"></div>',
  iconSize: [15, 15],
  iconAnchor: [7.5, 7.5]
});

// Helper component to auto-zoom to bounds
function MapBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export default function MapComponent({ routeData }) {
  const [userLocation, setUserLocation] = useState(null);

  // Watch user location for the blue dot
  useEffect(() => {
    const watchId = navigator.geolocation.watchPosition(
      (pos) => setUserLocation([pos.coords.latitude, pos.coords.longitude]),
      (err) => console.warn('Geolocation error:', err),
      { enableHighAccuracy: true, maximumAge: 5000 }
    );
    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Compute polyline and bounds
  const hasRoute = Boolean(routeData && routeData.stops && routeData.stops.length > 0);
  const polylinePositions = hasRoute ? routeData.stops.map(s => [s.lat, s.lon]) : [];
  
  let bounds = null;
  if (hasRoute) {
    bounds = L.latLngBounds(polylinePositions);
  } else if (userLocation) {
    bounds = L.latLngBounds([userLocation]);
  }

  // Default center of Mumbai
  const center = userLocation || [19.0760, 72.8777];

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '400px' }}>
      <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%', minHeight: '400px', borderRadius: 'inherit' }}>
        <TileLayer 
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        {userLocation && <Marker position={userLocation} icon={blueDotIcon} />}

        {hasRoute && (
          <Polyline 
            positions={polylinePositions} 
            pathOptions={{ 
              color: routeData.mode === 'metro' ? '#007bff' : '#28a745', 
              weight: 5 
            }} 
          />
        )}

        {hasRoute && routeData.stops.map(stop => (
          <Marker 
            key={stop.id} 
            position={[stop.lat, stop.lon]} 
            icon={routeData.mode === 'metro' ? metroIcon : busIcon}
          >
            <Popup>
              <strong>{stop.name}</strong><br/>
              {routeData.mode.toUpperCase()} Stop
            </Popup>
          </Marker>
        ))}

        {bounds && <MapBounds bounds={bounds} />}
      </MapContainer>
    </div>
  );
}
