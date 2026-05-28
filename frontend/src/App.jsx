import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import BookingPage from './pages/BookingPage';
import MyBookingsPage from './pages/MyBookingsPage';
import './index.css';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentPage, setCurrentPage] = useState('home');

  useEffect(() => {
    if (!token) {
      setCurrentPage('login');
    }
  }, [token]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentPage('login');
  };

  if (!token) {
    return <LoginPage onLoginSuccess={(t) => {
      localStorage.setItem('token', t);
      setToken(t);
      setCurrentPage('home');
    }} />;
  }

  return (
    <div className="app">
      {currentPage !== 'home' && (
        <header className="navbar">
          <h1 onClick={() => setCurrentPage('home')} style={{cursor: 'pointer'}}>🚌 WAY Transit</h1>
          <nav>
            <button onClick={() => setCurrentPage('search')}>Search</button>
            <button onClick={() => setCurrentPage('bookings')}>My Bookings</button>
            <button onClick={handleLogout}>Logout</button>
          </nav>
        </header>
      )}

      <main className="container">
        {currentPage === 'home' && <HomePage token={token} onNavigate={setCurrentPage} onLogout={handleLogout} />}
        {currentPage === 'search' && <SearchPage token={token} onBook={(routeId) => {
          window.routeToBook = routeId;
          setCurrentPage('book');
        }} />}
        {currentPage === 'book' && <BookingPage token={token} routeId={window.routeToBook} onSuccess={() => setCurrentPage('home')} onCancel={() => setCurrentPage('search')} />}
        {currentPage === 'bookings' && <MyBookingsPage token={token} />}
      </main>
    </div>
  );
}
