import React from 'react';

const transportOptions = ['Bus', 'Train', 'Metro', 'Cab'];
const travelPreferences = [
  ['Fastest', true],
  ['Avoid crowd', true],
  ['Fewest Transfers', false],
  ['Cost effective', false],
  ['Most comfortable', true],
];

const notificationPreferences = [
  ['Delay Notifications', true],
  ['Nearby Service Alerts', true],
  ['App Updates', false],
];

export default function PreferencesPage({ onNavigate }) {
  return (
    <div className="design-screen design-screen--preferences">
      <div className="design-topbar">
        <button className="design-back" type="button" onClick={() => onNavigate('home')} aria-label="Back">‹</button>
        <h2 className="design-title">Preferences</h2>
        <span className="design-spacer" />
      </div>

      <div className="preferences-grid">
        <section className="preference-panel">
          <h3>Preferred transport modes</h3>
          <div className="mode-grid">
            {transportOptions.map((option) => (
              <div className="mode-tile" key={option}>
                <div className="mode-icon">{option === 'Bus' ? '🚌' : option === 'Train' ? '🚆' : option === 'Metro' ? '🚇' : '🚕'}</div>
                <span>{option}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="preference-panel">
          <h3>Walking Buffer Time</h3>
          <p>Add extra time for walking to/from stops</p>
          <div className="buffer-display">🚶 10 Mins</div>
          <div className="slider-track"><span className="slider-thumb" /></div>
        </section>

        <section className="preference-panel preference-panel--wide">
          <h3>How do you like to travel?</h3>
          <div className="toggle-list">
            {travelPreferences.map(([label, enabled]) => (
              <div className="toggle-row" key={label}>
                <span>{label}</span>
                <span className={`fake-switch ${enabled ? 'is-on' : ''}`} />
              </div>
            ))}
          </div>
        </section>

        <section className="preference-panel preference-panel--wide">
          <h3>Make it yours</h3>
          <div className="option-group">
            <strong>Theme:</strong>
            <div className="choice-row">
              <span className="choice-chip">Light</span>
              <span className="choice-chip choice-chip--active">Dark</span>
              <span className="choice-chip">Fun</span>
            </div>
          </div>
          <div className="option-group">
            <strong>Font Size:</strong>
            <div className="choice-row">
              <span className="choice-chip">Small</span>
              <span className="choice-chip choice-chip--active">Medium</span>
              <span className="choice-chip">Large</span>
            </div>
          </div>
          <div className="toggle-list">
            {notificationPreferences.map(([label, enabled]) => (
              <div className="toggle-row" key={label}>
                <span>{label}</span>
                <span className={`fake-switch ${enabled ? 'is-on' : ''}`} />
              </div>
            ))}
          </div>
        </section>

        <section className="two-up-row">
          <div className="preference-panel">
            <h3>Accessibility Needs</h3>
            <p>Select if applicable</p>
            <div className="select-pill">Wheelchair ▾</div>
          </div>
          <div className="preference-panel">
            <h3>Language Preference</h3>
            <p>Select your preferred app language</p>
            <div className="select-pill">English ▾</div>
          </div>
        </section>

        <section className="preference-panel preference-panel--wide">
          <h3>How Should the AI Talk To You</h3>
          <div className="option-group">
            <strong>Tone Selector:</strong>
            <div className="choice-row">
              <span className="choice-chip">Friendly</span>
              <span className="choice-chip choice-chip--active">Direct</span>
              <span className="choice-chip">Minimal</span>
            </div>
          </div>
          <div className="option-group">
            <strong>Prompt Style:</strong>
            <div className="choice-row">
              <span className="choice-chip">Ask Me First</span>
              <span className="choice-chip choice-chip--active">Auto-Suggest</span>
            </div>
          </div>
          <div className="toggle-row toggle-row--last">
            <span>Enable Smart Suggestions</span>
            <span className="fake-switch is-on" />
          </div>
        </section>

        <section className="preference-panel preference-panel--wide">
          <h3>Smart Saver</h3>
          <div className="toggle-list">
            {[
              ['Offline Mode Only', true],
              ['Auto-Update Timetables', true],
              ['Low Data Mode', false],
            ].map(([label, enabled]) => (
              <div className="toggle-row" key={label}>
                <span>{label}</span>
                <span className={`fake-switch ${enabled ? 'is-on' : ''}`} />
              </div>
            ))}
          </div>
          <button className="download-pill" type="button">⬇️ Manage Downloads</button>
        </section>
      </div>
    </div>
  );
}