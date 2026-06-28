import React, { useState } from 'react';
import MapComponent from '../components/MapComponent';
import './HomePage.css';

export default function HomePage({ onNavigate }) {
  const [activeView, setActiveView] = useState('home');
  const [touchStart, setTouchStart] = useState(null);

  const handleTouchStart = (e) => setTouchStart(e.targetTouches[0].clientX);
  
  const handleTouchEnd = (e) => {
    if (!touchStart) return;
    const distance = touchStart - e.changedTouches[0].clientX;
    if (activeView === 'home' && distance > 50) setActiveView('profile');
    if (activeView === 'home' && distance < -50) setActiveView('ai');
    if (activeView === 'profile' && distance < -50) setActiveView('home');
    if (activeView === 'ai' && distance > 50) setActiveView('home');
    setTouchStart(null);
  };

  return (
    <div onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd} className="home-wrapper">
      {activeView === 'profile' && <ProfileView />}
      {activeView === 'home' && <HomeMainView onNavigate={onNavigate} />}
      {activeView === 'ai' && <AIHelperView />}
    </div>
  );
}

function HomeMainView({ onNavigate }) {
  return (
    <section className="home-container">
      <HomeHeader onNavigate={onNavigate} />
      {/* Flight Card removed to match Node 3:1871 */}
      <MapSearchArea onNavigate={onNavigate} />
      <ChatCategory />
      <TravelSavings />
      <Recommendations />
    </section>
  );
}

function HomeHeader({ onNavigate }) {
  return (
    <div className="home-header-new">
      <div className="home-greeting">
        <span className="wave">👋</span>
        <span className="greeting-text">HelloDaniel!</span>
      </div>
      <div className="home-header-icons">
        <button className="icon-btn-round">📅</button>
        <button className="icon-btn-round" onClick={() => onNavigate('bookings')}>🔔</button>
      </div>
    </div>
  );
}

function MapSearchArea({ onNavigate }) {
  return (
    <div className="map-search-area">
      <div className="map-wrapper">
        <MapComponent useDefaultStyle={true} />
        <div className="temperature-pill">32°C ☀️</div>
      </div>
      <div className="search-overlay" onClick={() => onNavigate('search')}>
        <span className="search-icon">🔍</span>
        <span className="search-placeholder">Where to?</span>
      </div>
    </div>
  );
}

function ChatCategory() {
  return (
    <div className="chat-category-section">
      <div className="chat-header">
        <span className="chat-logo">✨</span>
        <div className="chat-title">
          <span>Ai lorem lorem</span>
          <span className="chat-date">19'Mar'26 | 11:36</span>
        </div>
      </div>
      <div className="chat-dropdown">
        <span>Chat Category</span>
        <span>⌄</span>
      </div>
      <div className="chat-cards">
        <div className="chat-card suggested">
          <span>Suggested Chat</span>
          <h3>Aesthetic Cafés Near You ↗</h3>
        </div>
        <div className="chat-card planning">
          <span>Continue Planning</span>
          <h3>Get Away Weekend Trip ↗</h3>
        </div>
      </div>
    </div>
  );
}

function TravelSavings() {
  return (
    <div className="travel-savings">
      <div className="savings-header">
        <span>Travel Savings</span>
        <div className="savings-month">May, 2026 ⌄</div>
      </div>
      <div className="savings-amount">
        <h2>₹45</h2>
        <span>Saved</span>
      </div>
      <div className="savings-progress">
        <div className="progress-bar"><div className="progress-fill"></div></div>
        <div className="progress-labels"><span>Trips</span><span>Reward</span></div>
      </div>
      <button className="history-btn">Check Travel History ↗</button>
    </div>
  );
}

function Recommendations() {
  return (
    <div className="recommendations">
      <div className="rec-search">
        <span className="search-icon">🔍</span>
        <input type="text" placeholder="Recommendations For You...." />
        <button className="filter-btn">⚙️</button>
      </div>
      <div className="rec-tags">
        <button className="tag active">For You</button>
        <button className="tag">Trending</button>
        <button className="tag">Live Events</button>
      </div>
      <div className="event-card">
        <div className="event-info">
          <h3>Event Name</h3>
          <span>14 May, 2026 | 4.2 ★</span>
        </div>
        <button className="swipe-book-btn">Swipe to Book Trip &gt;&gt;</button>
      </div>
    </div>
  );
}

function ProfileView() {
  return (
    <section className="profile-container">
      <ProfileHeader />
      <StudentPass />
      <TravelDiary />
      <ProfileStats />
      <ProfileMenu />
    </section>
  );
}

function ProfileHeader() {
  return (
    <>
      <div className="profile-header">
        <div className="avatar">👩‍🎨</div>
        <h2>Daniel Smith</h2>
        <p>📍 Navi Mumbai | 32 Trips</p>
      </div>
      <div className="profile-cards">
        <div className="p-card">Documents ↗</div>
        <div className="p-card">Help ↗</div>
        <div className="p-card">FAQ ↗</div>
      </div>
    </>
  );
}

function StudentPass() {
  return (
    <div className="student-pass-card">
      <div className="pass-header">
        <span className="pass-train">12S Churchgate</span>
        <span className="pass-class">II Class</span>
        <span className="pass-platform">P3 Platform</span>
      </div>
      <div className="qr-section">
        <h2>CHS</h2>
        <div className="qr-code">QR</div>
        <h2>BA</h2>
      </div>
      <p className="pass-validity">Student Pass<br/>02/07/2026 - 05/07/2026</p>
    </div>
  );
}

function TravelDiary() {
  return (
    <>
      <div className="travel-diary">
        <h3>Your travel diary 📓</h3>
        <p>Relive your journeys - places you've been...</p>
        <button className="view-all-btn">View All</button>
      </div>
      <div className="profile-actions">
        <div className="action-box">Booking History ↗</div>
        <div className="action-box">Goals & Rewards ↗</div>
      </div>
    </>
  );
}

function ProfileStats() {
  return (
    <div className="stats-box">
      <h2>23hrs <span className="saved-text">Saved</span></h2>
      <p>38.5 km across 32 trips / 50 trips</p>
      <div className="trip-modes-bar">
        <div className="mode bus">🚌</div>
        <div className="mode train">🚆</div>
      </div>
    </div>
  );
}

function ProfileMenu() {
  return (
    <div className="bottom-actions">
       <button className="menu-btn">↗ Way Offline</button>
       <button className="menu-btn">Logout</button>
       <button className="menu-btn danger">Delete Account</button>
    </div>
  );
}

function AIHelperView() {
  return (
    <section className="ai-helper-container">
      <div className="ai-header">
        <h1>How can we<br/>help you?</h1>
        <p>50°C | 19'Mar'26 | 11:36</p>
      </div>
      <div className="ai-bubbles">
        <div className="ai-bubble plan-new">Plan a new<br/>Journey 💼 ↗</div>
        <div className="ai-bubble plan-weekend">Plan Weekend<br/>Trek 💼 ↗</div>
        <div className="ai-bubble start-group">Start a Group<br/>Chat 💬 ↗</div>
      </div>
      <div className="ask-ai-bar">
        <span className="ai-icon">✨</span>
        <input type="text" placeholder="Ask AI" />
        <span className="mic-icon">🎤</span>
      </div>
    </section>
  );
}
