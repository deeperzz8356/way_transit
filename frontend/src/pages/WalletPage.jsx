import React, { useEffect, useState } from 'react';
import './WalletPage.css';

export default function WalletPage() {
    const [tickets, setTickets] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchTickets();
    }, []);

    const fetchTickets = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('http://localhost:8000/booking/my-bookings', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!res.ok) throw new Error("Failed to fetch wallet tickets");
            const data = await res.json();
            setTickets(data);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="wallet-page">
            <header className="wallet-header">
                <h1>My Unified Wallet</h1>
                <p>Manage all your passes and tickets in one place.</p>
            </header>
            
            {error && <div className="error-message">{error}</div>}
            
            <div className="ticket-grid">
                {tickets.length === 0 && !error ? (
                    <div className="empty-wallet">Your wallet is empty. Add a ticket to get started!</div>
                ) : (
                    tickets.map(ticket => (
                        <div key={ticket.id} className="ticket-card">
                            <div className="ticket-info">
                                <h3>{ticket.source || 'Unknown'} ➔ {ticket.destination || 'Unknown'}</h3>
                                <p className="status">Status: {ticket.status}</p>
                                <p className="date">Added on: {new Date(ticket.booked_at).toLocaleDateString()}</p>
                                {ticket.image_url && <img src={ticket.image_url} alt="Scanned Ticket" className="scanned-thumbnail" />}
                            </div>
                            <div className="qr-section">
                                <img 
                                    src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${ticket.ticket_code}`} 
                                    alt="QR Code" 
                                    className="qr-code" 
                                />
                                <p className="ticket-code">{ticket.ticket_code?.substring(0,8).toUpperCase()}</p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
