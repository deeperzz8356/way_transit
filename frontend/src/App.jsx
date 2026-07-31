import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import AddTicketPage from './pages/AddTicketPage';
import WalletPage from './pages/WalletPage';
import ProfilePage from './pages/ProfilePage';
import PreferencesPage from './pages/PreferencesPage';
import TripHistoryPage from './pages/TripHistoryPage';
import AgenticPage from './pages/AgenticPage';
import Dashboard from './pages/dashboard/Dashboard';
import './index.css';
import MapComponent from './components/MapComponent';


export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [currentPage, setCurrentPage] = useState('home');

  const handleLoginSuccess = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentPage('home');
  };

  if (!token || token === 'dummy_token') {
    return (
      <div className="app">
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return (
    <div className="app">
      {currentPage !== 'home' && (
        <header className="navbar">
          <h1 onClick={() => setCurrentPage('home')} style={{cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <img src="/Group 1485.png" alt="WAY Logo" style={{ height: '32px' }} /> Transit
          </h1>
          <nav>
            <button onClick={() => setCurrentPage('add-ticket')}>Add Ticket</button>
            <button onClick={() => setCurrentPage('wallet')}>Unified Wallet</button>
            <button onClick={() => setCurrentPage('history')}>Trip History</button>
            <button onClick={() => setCurrentPage('profile')}>Profile</button>
            <button onClick={() => setCurrentPage('preferences')}>Preferences</button>
            <button onClick={() => setCurrentPage('agentic')}>Agentic AI</button>
            <button onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
            <button onClick={handleLogout}>Logout</button>
          </nav>
        </header>
      )}

      <main className="container">
        {/* Global map preview on main page */}

        {currentPage === 'home' && <HomePage token={token} onNavigate={setCurrentPage} onLogout={handleLogout} />}
        {currentPage === 'search' && <SearchPage token={token} onBook={(routeId) => {
          window.routeToBook = routeId;
          setCurrentPage('add-ticket');
        }} />}
        {currentPage === 'add-ticket' && <AddTicketPage token={token} onNavigate={setCurrentPage} />}
        {currentPage === 'wallet' && <WalletPage token={token} />}
        {currentPage === 'profile' && <ProfilePage onNavigate={setCurrentPage} />}
        {currentPage === 'preferences' && <PreferencesPage onNavigate={setCurrentPage} />}
        {currentPage === 'history' && <TripHistoryPage onNavigate={setCurrentPage} />}
        {currentPage === 'agentic' && <AgenticPage />}
        {currentPage === 'dashboard' && <Dashboard />}
      </main>
    </div>
  );
}
