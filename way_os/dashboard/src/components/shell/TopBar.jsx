import { useEffect, useState } from 'react';
import SegmentedControl from '../ui/SegmentedControl';
import './TopBar.css';

export default function TopBar({ city, role, onRoleChange }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="top-bar">
      <div className="top-bar__left">
        <h1 className="top-bar__brand">
          Transit<span>OS</span>
        </h1>
        <span className="top-bar__divider" aria-hidden />
        <span className="top-bar__city">{city}</span>
        <span className="top-bar__live">
          <span className="top-bar__live-dot" aria-hidden />
          Live demo
        </span>
      </div>
      <div className="top-bar__right">
        <SegmentedControl
          size="sm"
          layoutGroup="role"
          value={role}
          onChange={onRoleChange}
          options={[
            { value: 'operator', label: 'Operator' },
            { value: 'municipality', label: 'City' },
          ]}
        />
        <time className="top-bar__clock" dateTime={now.toISOString()}>
          {now.toLocaleString('en-IN', {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })}
        </time>
      </div>
    </header>
  );
}
