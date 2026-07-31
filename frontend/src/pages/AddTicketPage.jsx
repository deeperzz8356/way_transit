import React, { useState } from 'react';
import './AddTicketPage.css';

export default function AddTicketPage({ onNavigate }) {
    const [source, setSource] = useState('');
    const [destination, setDestination] = useState('');
    const [imagePreview, setImagePreview] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [transitMap, setTransitMap] = useState(null);
    const [error, setError] = useState(null);

    const handlePhotoUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            setImagePreview(url);
            
            // Mock OCR scanning process
            setIsScanning(true);
            setTimeout(() => {
                setSource('Downtown Station');
                setDestination('Airport Terminal 1');
                setIsScanning(false);
                generateTextMap('Downtown Station', 'Airport Terminal 1');
            }, 1500);
        }
    };

    const handleManualEntry = (e) => {
        e.preventDefault();
        if (source && destination) {
            generateTextMap(source, destination);
        }
    };

    const generateTextMap = (src, dest) => {
        // Mock text-based transit map timeline
        setTransitMap([
            { id: 1, type: 'walk', label: `Walk to ${src}` },
            { id: 2, type: 'transit', label: 'Take Metro Line Blue' },
            { id: 3, type: 'transit', label: `Arrive at ${dest}` }
        ]);
    };

    const handleSaveTicket = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/booking/add-ticket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    source,
                    destination,
                    image_url: imagePreview
                })
            });

            if (!res.ok) throw new Error("Failed to save ticket to wallet");
            
            onNavigate('wallet');
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="add-ticket-page">
            <div className="add-ticket-container">
                <h1>Add Ticket or Pass</h1>
                <p>Take a photo of your physical ticket or enter it manually to add it to your wallet.</p>
                
                {error && <div className="error-message">{error}</div>}

                <div className="upload-section">
                    <h3>Quick Photo Scanner</h3>
                    <label className="file-upload-btn">
                        Upload Ticket Photo
                        <input type="file" accept="image/*" onChange={handlePhotoUpload} hidden />
                    </label>
                    {isScanning && <p className="scanning-text">Scanning ticket... please wait.</p>}
                    {imagePreview && <img src={imagePreview} alt="Preview" className="image-preview" />}
                </div>

                <div className="divider"><span>OR</span></div>

                <div className="manual-section">
                    <h3>Manual Entry</h3>
                    <form onSubmit={handleManualEntry} className="manual-form">
                        <input 
                            type="text" 
                            placeholder="Source Station" 
                            value={source} 
                            onChange={(e) => setSource(e.target.value)} 
                        />
                        <input 
                            type="text" 
                            placeholder="Destination Station" 
                            value={destination} 
                            onChange={(e) => setDestination(e.target.value)} 
                        />
                        <button type="submit" className="map-btn">Show Route Map</button>
                    </form>
                </div>

                {transitMap && (
                    <div className="transit-map-section">
                        <h3>Active Transit Route</h3>
                        <div className="text-map">
                            {transitMap.map((step, index) => (
                                <div key={step.id} className="map-step">
                                    <div className={`step-icon ${step.type}`}></div>
                                    <p>{step.label}</p>
                                    {index < transitMap.length - 1 && <div className="step-line"></div>}
                                </div>
                            ))}
                        </div>
                        <button onClick={handleSaveTicket} className="save-btn">Save to Wallet</button>
                    </div>
                )}
            </div>
        </div>
    );
}
