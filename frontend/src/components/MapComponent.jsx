import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow });
L.Marker.prototype.options.icon = DefaultIcon;

const greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  iconSize: [25, 41], iconAnchor: [12, 41]
});

const orangeIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  iconSize: [25, 41], iconAnchor: [12, 41]
});

const blueDotIcon = new L.DivIcon({
  className: 'blue-pulsing-dot',
  html: '<div style="width: 15px; height: 15px; background: #007bff; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #007bff;"></div>',
  iconSize: [15, 15],
  iconAnchor: [7.5, 7.5]
});

function MapBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [50, 50] });
  }, [bounds, map]);
  return null;
}

export default function MapComponent({ source, destination, onRouteFound }) {
  const [routeGeo, setRouteGeo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userLocation, setUserLocation] = useState(null);
  const [geoWarning, setGeoWarning] = useState('');
  const [parsedSource, setParsedSource] = useState(null);
  const [parsedDest, setParsedDest] = useState(null);

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (pos.coords.accuracy > 100) setGeoWarning("Low GPS accuracy. Move to open area for better results.");
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) setGeoWarning("Location access denied. Enable location in browser settings.");
      }
    );

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        if (pos.coords.accuracy <= 100) setGeoWarning('');
      },
      (err) => console.warn('Geolocation error:', err),
      { enableHighAccuracy: true, maximumAge: 5000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  useEffect(() => {
    async function resolveLocations() {
      let s = null, d = null;
      if (source && typeof source === 'object' && source.lat) s = source;
      else if (typeof source === 'string') s = await geocodeString(source);
      
      if (destination && typeof destination === 'object' && destination.lat) d = destination;
      else if (typeof destination === 'string') d = await geocodeString(destination);
      
      setParsedSource(s);
      setParsedDest(d);
    }
    resolveLocations();
  }, [source, destination]);

  useEffect(() => {
    if (parsedSource?.lat && parsedDest?.lat) {
      fetchRouteData(parsedSource, parsedDest, setRouteGeo, setLoading, setError, onRouteFound);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parsedSource?.lat, parsedSource?.lng, parsedDest?.lat, parsedDest?.lng]);

  return renderMapState(parsedSource, parsedDest, routeGeo, loading, error, userLocation, geoWarning);
}

async function geocodeString(query) {
  if (!query || typeof query !== 'string') return null;
  try {
    const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&format=json`);
    const data = await res.json();
    if (!data.results || data.results.length === 0) return null;
    return { lat: data.results[0].latitude, lng: data.results[0].longitude, name: query };
  } catch (err) {
    console.warn('Geocoding failed for', query, err);
    return null;
  }
}

async function fetchRouteData(src, dst, setRouteGeo, setLoading, setError, onRouteFound) {
  setLoading(true);
  setError('');
  try {
    const url = `https://router.project-osrm.org/route/v1/driving/${src.lng},${src.lat};${dst.lng},${dst.lat}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.code !== 'Ok') throw new Error('Route not found');
    const route = data.routes[0];
    const coords = route.geometry.coordinates.map(c => [c[1], c[0]]);
    setRouteGeo(coords);
    if (onRouteFound) onRouteFound({ distance: (route.distance / 1000).toFixed(2), duration: Math.round(route.duration / 60) });
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}

function MapLayers({ hasValidRoute, source, destination, userLocation, routeGeo, bounds }) {
  return (
    <>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {hasValidRoute ? <Marker position={[source.lat, source.lng]} icon={greenIcon} /> : null}
      {hasValidRoute ? <Marker position={[destination.lat, destination.lng]} icon={orangeIcon} /> : null}
      {userLocation ? <Marker position={userLocation} icon={blueDotIcon} /> : null}
      {routeGeo ? <Polyline positions={routeGeo} pathOptions={{ color: '#1D9E75', weight: 4 }} /> : null}
      {bounds ? <MapBounds bounds={bounds} /> : null}
    </>
  );
}

function renderMapState(source, destination, routeGeo, loading, error, userLocation, geoWarning) {
  if (error) return <div className="error" style={{ padding: '20px' }}>{error}</div>;

  const hasValidRoute = Boolean(source?.lat && destination?.lat);
  const center = hasValidRoute ? [source.lat, source.lng] : (userLocation || [19.0760, 72.8777]);
  const zoom = hasValidRoute ? 13 : 11;
  const bounds = routeGeo ? L.latLngBounds(routeGeo) : (hasValidRoute ? L.latLngBounds([[source.lat, source.lng], [destination.lat, destination.lng]]) : null);
  
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '400px' }}>
      {geoWarning ? (
        <div style={{
          position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)',
          zIndex: 1000, background: '#ffcc00', padding: '8px 16px', borderRadius: '4px',
          fontWeight: 'bold', color: '#333', boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          {geoWarning}
        </div>
      ) : null}
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%', minHeight: '400px', borderRadius: 'inherit' }}>
        <MapLayers 
          hasValidRoute={hasValidRoute} 
          source={source} 
          destination={destination} 
          userLocation={userLocation} 
          routeGeo={routeGeo} 
          bounds={bounds} 
        />
      </MapContainer>
    </div>
  );
}
