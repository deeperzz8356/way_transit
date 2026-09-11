import React, { useState, useEffect, useRef, useCallback } from 'react';
import MapComponent from '../components/MapComponent';
import './SearchPage.css';

const API_BASE = 'http://localhost:8000';

// ── Utility ──────────────────────────────────────────────────────────────────

/** Format HH:MM:SS or HH:MM to a readable "8:05 AM" string. */
function fmtTime(t) {
  if (!t) return '—';
  const [h, m] = t.split(':').map(Number);
  const ampm = h < 12 ? 'AM' : 'PM';
  const h12 = h % 12 || 12;
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
}

/** Compute "Xhr Ymin" duration between two HH:MM(:SS) strings. */
function calcDuration(dep, arr) {
  if (!dep || !arr) return null;
  const toMin = (t) => {
    const [h, m] = t.split(':').map(Number);
    return h * 60 + m;
  };
  let diff = toMin(arr) - toMin(dep);
  if (diff < 0) diff += 24 * 60; // overnight
  if (diff === 0) return null;
  const h = Math.floor(diff / 60);
  const m = diff % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

/** Mode → emoji + label */
const MODE_META = {
  train:  { emoji: '🚆', label: 'Train',  color: '#e84393' },
  metro:  { emoji: '🚝', label: 'Metro',  color: '#007bff' },
  bus:    { emoji: '🚌', label: 'Bus',    color: '#28a745' },
};
function modeMeta(m) {
  return MODE_META[m?.toLowerCase()] || { emoji: '🚌', label: m || 'Transit', color: '#666' };
}

// ── Autocomplete hook ─────────────────────────────────────────────────────────

function useStopSearch(debounceMs = 300) {
  const [query, setQuery]           = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading]       = useState(false);
  const [selected, setSelected]     = useState(null); // StopResult | null
  const timerRef                    = useRef(null);

  const handleInput = useCallback((val) => {
    setQuery(val);
    setSelected(null);
    clearTimeout(timerRef.current);
    if (val.trim().length < 2) { setSuggestions([]); return; }
    timerRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/search/stops?q=${encodeURIComponent(val)}&limit=8`);
        if (!res.ok) throw new Error('fetch failed');
        const data = await res.json();
        setSuggestions(data);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, debounceMs);
  }, [debounceMs]);

  const pick = useCallback((stop) => {
    setSelected(stop);
    setQuery(stop.name);
    setSuggestions([]);
  }, []);

  const clear = useCallback(() => {
    setSelected(null);
    setQuery('');
    setSuggestions([]);
  }, []);

  /** Swap contents with another hook's state. Returns new state for both. */
  const swapWith = useCallback((other) => {
    const myStop  = selected;
    const myQuery = query;
    setSelected(other.selected);
    setQuery(other.selected ? other.selected.name : other.query);
    setSuggestions([]);
    other.setSelected(myStop);
    other.setQuery(myStop ? myStop.name : myQuery);
    other.setSuggestions([]);
  }, [selected, query]);

  return { query, setQuery, suggestions, setSuggestions, loading, selected, setSelected, handleInput, pick, clear, swapWith };
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SearchPage({ token, onBook }) {
  const src = useStopSearch();
  const dst = useStopSearch();

  const [activeMode, setActiveMode]     = useState('all');  // 'all' | 'train' | 'metro' | 'bus'
  const [results, setResults]           = useState([]);
  const [searchMsg, setSearchMsg]       = useState('');
  const [hasSearched, setHasSearched]   = useState(false);
  const [searching, setSearching]       = useState(false);

  const [selectedTripRouteId, setSelectedTripRouteId] = useState(null);
  const [routeData, setRouteData]                     = useState(null);

  // ── Fetch map path when a trip's route is selected ────────────────────────
  useEffect(() => {
    if (!selectedTripRouteId) { setRouteData(null); return; }
    fetch(`${API_BASE}/search/route/${selectedTripRouteId}/path`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setRouteData(d))
      .catch(() => setRouteData(null));
  }, [selectedTripRouteId]);

  // ── Swap source ↔ destination ─────────────────────────────────────────────
  function swapStops() {
    const srcStop  = src.selected;
    const srcQuery = src.query;
    src.setSelected(dst.selected);
    src.setQuery(dst.selected ? dst.selected.name : dst.query);
    src.setSuggestions([]);
    dst.setSelected(srcStop);
    dst.setQuery(srcStop ? srcStop.name : srcQuery);
    dst.setSuggestions([]);
    setResults([]);
    setSearchMsg('');
    setHasSearched(false);
    setSelectedTripRouteId(null);
  }

  // ── Search ────────────────────────────────────────────────────────────────
  const canSearch = src.selected && dst.selected && !searching;

  async function doSearch() {
    if (!canSearch) return;
    if (src.selected.id === dst.selected.id) {
      setSearchMsg('Source and destination cannot be the same stop.');
      setResults([]);
      setHasSearched(true);
      return;
    }
    setSearching(true);
    setResults([]);
    setSearchMsg('');
    setHasSearched(true);
    setSelectedTripRouteId(null);
    setRouteData(null);
    try {
      const body = {
        source_stop_id: src.selected.id,
        destination_stop_id: dst.selected.id,
        ...(activeMode !== 'all' ? { mode: activeMode } : {}),
      };
      const res = await fetch(`${API_BASE}/search/trips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setSearchMsg(err.detail || 'Search failed. Please try again.');
        return;
      }
      const data = await res.json();
      setResults(data.results || []);
      setSearchMsg(data.message || '');
      if (data.results?.length > 0) {
        setSelectedTripRouteId(data.results[0].route_id);
      }
    } catch (e) {
      setSearchMsg('Network error. Is the backend running?');
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="search-page-wrapper">
      <div className="map-background">
        <MapComponent routeData={routeData} />
      </div>

      <TopOverlay
        src={src}
        dst={dst}
        activeMode={activeMode}
        onModeChange={setActiveMode}
        onSwap={swapStops}
        onSearch={doSearch}
        canSearch={canSearch}
        searching={searching}
      />

      <BottomSheet
        results={results}
        message={searchMsg}
        hasSearched={hasSearched}
        loading={searching}
        selectedTripRouteId={selectedTripRouteId}
        onSelectTrip={(trip) => setSelectedTripRouteId(trip.route_id)}
        onBook={onBook}
      />
    </div>
  );
}

// ── Top overlay: stop inputs + mode tabs + swap ───────────────────────────────

function TopOverlay({ src, dst, activeMode, onModeChange, onSwap, onSearch, canSearch, searching }) {
  const srcRef = useRef(null);
  const dstRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handler(e) {
      if (!srcRef.current?.contains(e.target)) src.setSuggestions([]);
      if (!dstRef.current?.contains(e.target)) dst.setSuggestions([]);
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [src, dst]);

  return (
    <div className="search-overlay-top">
      <div className="route-header-card">

        {/* ── Stop input row ── */}
        <div className="stop-input-row">
          {/* Source */}
          <div className="stop-field-wrap" ref={srcRef}>
            <StopField
              value={src.query}
              placeholder="From — e.g. Thane"
              isSelected={!!src.selected}
              loading={src.loading}
              dotColor="#28a745"
              onChange={src.handleInput}
              onClear={src.clear}
            />
            {src.suggestions.length > 0 && (
              <SuggestionDropdown stops={src.suggestions} onPick={src.pick} />
            )}
          </div>

          {/* Swap button */}
          <button
            className="swap-btn"
            onClick={onSwap}
            title="Swap source and destination"
            aria-label="Swap source and destination"
          >
            ⇄
          </button>

          {/* Destination */}
          <div className="stop-field-wrap" ref={dstRef}>
            <StopField
              value={dst.query}
              placeholder="To — e.g. Panvel"
              isSelected={!!dst.selected}
              loading={dst.loading}
              dotColor="#e84393"
              onChange={dst.handleInput}
              onClear={dst.clear}
            />
            {dst.suggestions.length > 0 && (
              <SuggestionDropdown stops={dst.suggestions} onPick={dst.pick} />
            )}
          </div>
        </div>

        {/* ── Mode filter + Search ── */}
        <div className="mode-search-row">
          <ModeTabs active={activeMode} onChange={onModeChange} />
          <button
            className={`search-btn ${canSearch ? 'active' : 'disabled'}`}
            onClick={onSearch}
            disabled={!canSearch}
          >
            {searching ? <span className="spinner" /> : '🔍 Search'}
          </button>
        </div>

      </div>
    </div>
  );
}

// ── Individual stop input field ───────────────────────────────────────────────

function StopField({ value, placeholder, isSelected, loading, dotColor, onChange, onClear }) {
  return (
    <div className={`stop-field ${isSelected ? 'resolved' : ''}`}>
      <span className="stop-dot" style={{ background: dotColor }} />
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={e => onChange(e.target.value)}
        className="stop-input"
        autoComplete="off"
        spellCheck={false}
      />
      {loading && <span className="field-spinner" />}
      {!loading && value && (
        <button className="field-clear" onClick={onClear} aria-label="Clear">✕</button>
      )}
    </div>
  );
}

// ── Autocomplete dropdown ─────────────────────────────────────────────────────

function SuggestionDropdown({ stops, onPick }) {
  return (
    <ul className="suggestion-dropdown" role="listbox">
      {stops.map(stop => {
        const mm = modeMeta(stop.mode);
        return (
          <li
            key={stop.id}
            className="suggestion-item"
            role="option"
            onMouseDown={() => onPick(stop)}  // mousedown fires before blur
          >
            <span className="sugg-emoji">{mm.emoji}</span>
            <span className="sugg-name">{stop.name}</span>
            <span className="sugg-mode" style={{ color: mm.color }}>{mm.label}</span>
          </li>
        );
      })}
    </ul>
  );
}

// ── Transport mode tabs ───────────────────────────────────────────────────────

const MODES = [
  { key: 'all',   emoji: '🗺',  label: 'All'   },
  { key: 'train', emoji: '🚆', label: 'Train' },
  { key: 'metro', emoji: '🚝', label: 'Metro' },
  { key: 'bus',   emoji: '🚌', label: 'Bus'   },
];

function ModeTabs({ active, onChange }) {
  return (
    <div className="mode-tabs" role="tablist" aria-label="Transport mode">
      {MODES.map(m => (
        <button
          key={m.key}
          role="tab"
          aria-selected={active === m.key}
          className={`mode-tab ${active === m.key ? 'active' : ''}`}
          onClick={() => onChange(m.key)}
        >
          <span>{m.emoji}</span>
          <span className="mode-tab-label">{m.label}</span>
        </button>
      ))}
    </div>
  );
}

// ── Bottom sheet ──────────────────────────────────────────────────────────────

function BottomSheet({ results, message, hasSearched, loading, selectedTripRouteId, onSelectTrip, onBook }) {
  return (
    <div className="search-bottom-sheet">
      <div className="sheet-handle" />
      <div className="journey-list">
        {loading && (
          <div className="sheet-status">
            <span className="spinner large" /> Finding services…
          </div>
        )}

        {!loading && !hasSearched && (
          <div className="sheet-hint">
            Enter a source and destination above, then tap Search.
          </div>
        )}

        {!loading && hasSearched && results.length === 0 && (
          <div className="sheet-status">{message || 'No services found.'}</div>
        )}

        {!loading && results.length > 0 && (
          <>
            <p className="sheet-count">{message}</p>
            {results.map(trip => (
              <TripCard
                key={trip.trip_id}
                trip={trip}
                isSelected={trip.route_id === selectedTripRouteId}
                onSelect={() => onSelectTrip(trip)}
                onBook={() => onBook && onBook(trip.route_id)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

// ── Trip result card ──────────────────────────────────────────────────────────

function TripCard({ trip, isSelected, onSelect, onBook }) {
  const mm       = modeMeta(trip.mode);
  const dep      = fmtTime(trip.source.departure_time);
  const arr      = fmtTime(trip.destination.arrival_time);
  const duration = calcDuration(trip.source.departure_time, trip.destination.arrival_time);

  return (
    <div
      className={`trip-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onSelect()}
    >
      {/* Mode badge */}
      <div className="trip-mode-badge" style={{ background: mm.color + '18', color: mm.color }}>
        <span>{mm.emoji}</span>
        <span className="trip-mode-label">{mm.label}</span>
      </div>

      {/* Route / trip info */}
      <div className="trip-info">
        <div className="trip-name">{trip.route_name || trip.trip_name}</div>
        {trip.operator_name && (
          <div className="trip-operator">{trip.operator_name}</div>
        )}
        {trip.direction && (
          <div className="trip-direction">Direction: {trip.direction}</div>
        )}
      </div>

      {/* Times */}
      <div className="trip-times">
        <div className="time-row">
          <span className="time-dep">{dep}</span>
          <span className="time-arrow">→</span>
          <span className="time-arr">{arr}</span>
        </div>
        {duration && <div className="trip-duration">{duration}</div>}
      </div>

      {/* Book button */}
      <button
        className="book-btn"
        onClick={e => { e.stopPropagation(); onBook(); }}
        aria-label={`Book ${trip.route_name}`}
      >
        Book
      </button>
    </div>
  );
}
