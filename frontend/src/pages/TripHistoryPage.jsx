import React from 'react';

const trips = [
  { source: 'Kurla', destination: 'Andheri', duration: '~ 45 minutes', bookmarked: false },
  { source: 'Kurla', destination: 'Andheri', duration: '~ 45 minutes', bookmarked: true },
  { source: 'Kurla', destination: 'Andheri', duration: '~ 45 minutes', bookmarked: true },
  { source: 'Kurla', destination: 'Andheri', duration: '~ 45 minutes', bookmarked: false },
];

const filters = ['Today', 'Last Week', 'Last Month'];

export default function TripHistoryPage({ onNavigate }) {
  return (
    <div className="design-screen design-screen--history">
      <div className="design-topbar">
        <button className="design-back" type="button" onClick={() => onNavigate('home')} aria-label="Back">‹</button>
        <h2 className="design-title">Trip History</h2>
        <span className="design-spacer" />
      </div>

      <section className="history-search-card">
        <div className="history-search">
          <span className="history-search__icon">⌕</span>
          <input type="text" placeholder="Search your trips..." aria-label="Search your trips" />
        </div>
        <div className="history-filters">
          {filters.map((filter) => (
            <button key={filter} type="button" className="history-filter-pill">
              <span>📅</span>{filter}
            </button>
          ))}
        </div>
      </section>

      <section className="history-list">
        {trips.map((trip, index) => (
          <article className="history-card" key={`${trip.source}-${trip.destination}-${index}`}>
            <div className="history-card__header">
              <h3>{trip.source} → {trip.destination}</h3>
              {trip.bookmarked ? <span className="bookmark-icon">🔖</span> : null}
            </div>
            <div className="history-duration">⏱ {trip.duration}</div>
            <div className="history-modes">
              <span>🚶</span>
              <span>🚌</span>
              <span>🚆</span>
            </div>
            <div className="history-footer">↩ Last Traveled: 2 days ago</div>
          </article>
        ))}
      </section>
    </div>
  );
}