import './StatusPill.css';

const TONE = {
  on_time: 'teal',
  delayed: 'amber',
  maintenance: 'red',
  idle: 'slate',
  high: 'red',
  medium: 'amber',
  low: 'teal',
  positive: 'teal',
  negative: 'red',
  neutral: 'slate',
  clear: 'teal',
  watch: 'amber',
  action: 'red',
  ready: 'teal',
  dispatched: 'teal',
  pre_trip: 'amber',
  queued: 'slate',
  awaiting_driver: 'amber',
  blocked: 'red',
  in_progress: 'teal',
  completed: 'slate',
};

export default function StatusPill({ status, label }) {
  const tone = TONE[status] || 'slate';
  return <span className={`status-pill status-pill--${tone}`}>{label || status}</span>;
}
