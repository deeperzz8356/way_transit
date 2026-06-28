import React, { useState, useEffect } from 'react';
import MapComponent from '../components/MapComponent';
import { calculateDuration } from '../utils/timeUtils';

export default function BookingPage({ token, routeId, onSuccess, onCancel }) {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bookingInProgress, setBookingInProgress] = useState(false);
  const [error, setError] = useState('');

  const [srcInput, setSrcInput] = useState('');
  const [destInput, setDestInput] = useState('');
  const [mapSource, setMapSource] = useState(null);
  const [mapDest, setMapDest] = useState(null);
  const [routeInfo, setRouteInfo] = useState(null);
  const [mapLoading, setMapLoading] = useState(false);
  const [mapError, setMapError] = useState('');

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    fetchRouteDetails(routeId, token, setRoute, setError, setLoading, API_URL);
  }, [routeId, token]);

  const handleBookAndPay = async () => {
    if (!routeInfo || !mapSource || !mapDest) return;
    setError('');
    setBookingInProgress(true);

    try {
      // 1. Create order
      const res = await fetch(`${API_URL}/booking/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          route_id: routeId || 1,
          source: mapSource.name,
          destination: mapDest.name,
          distance_km: parseFloat(routeInfo.distance)
        })
      });
      const orderData = await res.json();
      if (!res.ok) throw new Error(orderData.detail || 'Failed to create order');

      // 2. Load Razorpay script
      const scriptLoaded = await new Promise((resolve) => {
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
      });
      
      if (!scriptLoaded) throw new Error('Failed to load Razorpay SDK');

      // 3. Open Razorpay
      const options = {
        key: orderData.razorpay_key,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "Transit App",
        description: `${mapSource.name} → ${mapDest.name}`,
        order_id: orderData.order_id,
        handler: async function(response) {
          // 4. Verify Payment
          try {
            const verifyRes = await fetch(`${API_URL}/booking/verify-payment`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                booking_id: orderData.booking_id
              })
            });
            const verifyData = await verifyRes.json();
            if (!verifyRes.ok) throw new Error(verifyData.detail || 'Payment verification failed');
            
            alert(`✓ Booking confirmed successfully! Booking ID: ${orderData.booking_id}`);
            onSuccess();
          } catch (err) {
            setError(err.message);
          }
        },
        prefill: { name: "Transit User", email: "user@example.com" },
        theme: { color: "#1D9E75" }
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response){
        setError(`Payment failed: ${response.error.description}`);
      });
      rzp.open();
    } catch (err) {
      setError(err.message);
    } finally {
      setBookingInProgress(false);
    }
  };

  const handleFindRoute = async () => {
    setMapLoading(true);
    setMapError('');
    try {
      const sData = await geocode(srcInput);
      const dData = await geocode(destInput);
      setMapSource(sData);
      setMapDest(dData);
    } catch (err) {
      setMapError(err.message);
    } finally {
      setMapLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading booking details...</div>;
  if (error && !route) return renderError(error, onCancel);

  return renderPage(
    route, error, bookingInProgress, handleBookAndPay, onCancel,
    srcInput, setSrcInput, destInput, setDestInput, handleFindRoute,
    mapLoading, mapError, mapSource, mapDest, routeInfo, setRouteInfo
  );
}

async function fetchRouteDetails(routeId, token, setRoute, setError, setLoading, API_URL) {
  if (!routeId) {
    setError('No route selected');
    setLoading(false);
    return;
  }
  try {
    const res = await fetch(`${API_URL}/search/route/${routeId}`, { headers: { 'Authorization': `Bearer ${token}` } });
    const data = await res.json();
    if (res.ok) {
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

async function geocode(query) {
  const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&format=json`);
  const data = await res.json();
  if (!data.results || data.results.length === 0) throw new Error(`Location not found: ${query}`);
  return { lat: data.results[0].latitude, lng: data.results[0].longitude, name: query };
}

function renderError(error, onCancel) {
  return (
    <div className="booking-container">
      <h2>Confirm Booking</h2>
      <div className="error">{error}</div>
      <button onClick={onCancel} className="confirm-btn" style={{ backgroundColor: '#7f8c8d' }}>Back to Search</button>
    </div>
  );
}

function renderPage(
  route, error, bookingInProgress, handleBookAndPay, onCancel,
  srcInput, setSrcInput, destInput, setDestInput, handleFindRoute,
  mapLoading, mapError, mapSource, mapDest, routeInfo, setRouteInfo
) {
  return (
    <div className="booking-container confirmation-page">
      <h2>Confirm Booking</h2>
      {error && <div className="error" style={{background: '#f8d7da', color: '#721c24', padding: '10px', borderRadius: '4px', marginBottom: '15px'}}>{error}</div>}

      <div className="route-map-section" style={{ marginBottom: '20px', padding: '15px', background: '#f9f9f9', borderRadius: '8px', color: '#333' }}>
        <h3>Find Route on Map</h3>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
          <input value={srcInput} onChange={e => setSrcInput(e.target.value)} placeholder="Source" style={{ padding: '8px', flex: 1 }} />
          <input value={destInput} onChange={e => setDestInput(e.target.value)} placeholder="Destination" style={{ padding: '8px', flex: 1 }} />
          <button onClick={handleFindRoute} disabled={mapLoading} style={{ padding: '8px 16px' }}>
            {mapLoading ? 'Searching...' : 'Find Route'}
          </button>
        </div>
        {mapError && <div className="error">{mapError}</div>}
        {mapSource && mapDest && (
          <>
            <div style={{ height: '300px', width: '100%', marginBottom: '10px' }}>
              <MapComponent source={mapSource} destination={mapDest} onRouteFound={setRouteInfo} />
            </div>
            {routeInfo && (
              <div style={{ fontWeight: 'bold' }}>
                Distance: {routeInfo.distance} km | Estimated Time: {routeInfo.duration} min
              </div>
            )}
          </>
        )}
      </div>

      <div className="booking-layout">
        <div className="booking-details-panel">
          {renderBookingCard(route, mapSource, mapDest, routeInfo, bookingInProgress, handleBookAndPay, onCancel)}
        </div>
      </div>
    </div>
  );
}

function renderBookingCard(route, mapSource, mapDest, routeInfo, bookingInProgress, handleBookAndPay, onCancel) {
  const distance = routeInfo ? parseFloat(routeInfo.distance) : 0;
  const fare = routeInfo ? Math.round(10 + (2 * distance)) : 0;
  const canBook = !!routeInfo;

  return (
    <div className="booking-card summary-card">
      <div className="route-header">
        <span className="route-name">
          {mapSource ? mapSource.name : (route ? route.source : 'Source')} 
          &nbsp;→&nbsp; 
          {mapDest ? mapDest.name : (route ? route.destination : 'Destination')}
        </span>
      </div>
      
      <div className="booking-info-list" style={{ marginTop: '20px' }}>
        <div className="info-item">
          <span className="info-label">Distance</span>
          <span className="info-value">{distance > 0 ? `${distance} km` : '-'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Duration</span>
          <span className="info-value">{routeInfo ? `${routeInfo.duration} min` : '-'}</span>
        </div>
        <div className="info-item price-item">
          <span className="info-label">Calculated Fare</span>
          <span className="info-value price-text">₹{fare > 0 ? fare : '-'}</span>
        </div>
      </div>
      
      <div className="booking-actions">
        <button onClick={handleBookAndPay} disabled={!canBook || bookingInProgress} className="confirm-btn">
          {bookingInProgress ? 'Processing Payment...' : 'Book & Pay'}
        </button>
        <button onClick={onCancel} disabled={bookingInProgress} className="cancel-btn">Go Back</button>
      </div>
    </div>
  );
}
