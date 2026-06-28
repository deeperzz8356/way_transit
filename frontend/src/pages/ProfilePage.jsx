import React from 'react';

const recapStats = [
  { value: '32', label: 'Trips' },
  { value: '164 km', label: 'Distance' },
  { value: '8 hours', label: 'Time Saved' },
];

const shortcuts = [
  { title: 'Trip History', icon: '🕘', size: 'small' },
  { title: 'Downloaded Maps', icon: '⬇️', size: 'small' },
  { title: 'Tickets and Passes', icon: '🎫', size: 'large', description: 'View current tickets and passes' },
  { title: 'Way Offline', icon: '📡', size: 'wide', description: 'Your essential transit info saved' },
  { title: 'Emergency Information', icon: '🚨', size: 'tall', description: 'Your Safety Toolkit' },
  { title: 'Preferences', icon: '⚙️', size: 'small' },
  { title: 'Help Center', icon: '❓', size: 'small' },
];

export default function ProfilePage({ onNavigate }) {
  return (
    <div className="design-screen design-screen--profile">
      <div className="design-topbar">
        <button className="design-back" type="button" onClick={() => onNavigate('home')} aria-label="Back">
          ‹
        </button>
        <h2 className="design-title">Your Space</h2>
        <button className="design-edit" type="button" aria-label="Edit profile">
          ✎
        </button>
      </div>

      <section className="profile-hero">
        <div className="profile-avatar" aria-hidden="true" />
        <div className="profile-meta">
          <h3>Mahesh Shah</h3>
          <p>+91 81082 71319</p>
        </div>
      </section>

      <section className="recap-card">
        <h3>Your monthly recap</h3>
        <div className="recap-grid">
          {recapStats.map((item) => (
            <div className="recap-tile" key={item.label}>
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
        <p>You&apos;re ahead of 87% of your city!</p>
      </section>

      <section className="shortcut-grid">
        {shortcuts.map((item) => (
          <button
            key={item.title}
            type="button"
            className={`shortcut-card shortcut-card--${item.size}`}
            onClick={() => item.title === 'Trip History' ? onNavigate('history') : null}
          >
            <span className="shortcut-icon" aria-hidden="true">{item.icon}</span>
            <span className="shortcut-copy">
              <strong>{item.title}</strong>
              {item.description && <small>{item.description}</small>}
            </span>
          </button>
        ))}
      </section>

      <button className="logout-pill" type="button" onClick={() => onNavigate('home')}>
        Log Out
      </button>
    </div>
  );
}