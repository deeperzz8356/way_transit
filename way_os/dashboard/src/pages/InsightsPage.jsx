import { motion } from 'motion/react';
import { useTransitData } from '../context/TransitContext';
import StatusPill from '../components/ui/StatusPill';
import { useMotionBudget } from '../motion/budget';
import './page.css';

function ScoreRing({ label, value, tone, index }) {
  const { reduce, duration } = useMotionBudget();
  const r = 36;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  const color =
    tone === 'high' ? 'var(--teal)' : tone === 'mid' ? 'var(--amber)' : 'var(--red)';

  return (
    <motion.div
      className="score-ring"
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: duration(220), delay: reduce ? 0 : index * 0.05, ease: [0.16, 1, 0.3, 1] }}
    >
      <svg width="96" height="96" viewBox="0 0 96 96" aria-hidden>
        <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="7" />
        <motion.circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={reduce ? false : { strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: duration(500), delay: reduce ? 0 : 0.1 + index * 0.05, ease: [0.16, 1, 0.3, 1] }}
          transform="rotate(-90 48 48)"
        />
        <text
          x="48"
          y="52"
          textAnchor="middle"
          fill="var(--text)"
          fontSize="18"
          fontFamily="var(--font-display)"
          fontWeight="700"
        >
          {value}
        </text>
      </svg>
      <div className="score-ring__label">{label}</div>
    </motion.div>
  );
}

export default function InsightsPage() {
  const { insights, role, alerts } = useTransitData();
  const { scorecards, recommendations, municipalityExtras } = insights;
  const toneFor = (v) => (v >= 85 ? 'high' : v >= 70 ? 'mid' : 'low');

  return (
    <div className="page page--scroll">
      <div className="page__toolbar">
        <div>
          <h2 className="page__title">Insights</h2>
          <p className="page__sub">
            {role === 'municipality'
              ? 'City-wide performance and service recommendations'
              : 'Fleet scorecards and actionable recommendations'}
          </p>
        </div>
      </div>

      <div className="score-grid">
        <ScoreRing label="Vehicle health" value={scorecards.vehicleHealth} tone={toneFor(scorecards.vehicleHealth)} index={0} />
        <ScoreRing label="Service" value={scorecards.service} tone={toneFor(scorecards.service)} index={1} />
        <ScoreRing label="Driver" value={scorecards.driver} tone={toneFor(scorecards.driver)} index={2} />
        <ScoreRing label="Demand" value={scorecards.demand} tone={toneFor(scorecards.demand)} index={3} />
      </div>

      {role === 'municipality' && (
        <div className="ops-strip ops-strip--spaced">
          <div className="ops-strip__card">
            <div className="ops-strip__label">Coverage</div>
            <div className="ops-strip__value">{municipalityExtras.cityCoveragePct}%</div>
          </div>
          <div className="ops-strip__card">
            <div className="ops-strip__label">Peak corridors</div>
            <div className="ops-strip__value ops-strip__value--sm">
              {municipalityExtras.peakCorridors.join(' · ')}
            </div>
          </div>
          <div className="ops-strip__card">
            <div className="ops-strip__label">Service gaps</div>
            <div className="ops-strip__value ops-strip__value--sm">
              {municipalityExtras.serviceGaps.join(' · ')}
            </div>
          </div>
          <div className="ops-strip__card">
            <div className="ops-strip__label">Avg compliance</div>
            <div className="ops-strip__value">{municipalityExtras.operatorComplianceAvg}%</div>
          </div>
        </div>
      )}

      <h3 className="section-title">Recommendations</h3>
      <div className="rec-grid">
        {recommendations.map((rec) => (
          <article key={rec.id} className={`rec-card rec-card--${rec.severity}`}>
            <StatusPill status={rec.severity} label={rec.severity} />
            <h4>{rec.title}</h4>
            <div className="rec-card__entity">{rec.entity}</div>
            <p>{rec.description}</p>
            <p className="rec-card__action">{rec.recommendation}</p>
          </article>
        ))}
      </div>

      <h3 className="section-title section-title--gap">Maintenance alerts</h3>
      <div className="rec-grid">
        {alerts.map((a) => (
          <article
            key={a.id}
            className={`rec-card rec-card--${a.priority === 'high' ? 'high' : a.priority === 'medium' ? 'medium' : 'low'}`}
          >
            <StatusPill status={a.priority} label={a.priority} />
            <h4>{a.vehicleId}</h4>
            <div className="rec-card__entity">Due {a.dueDate}</div>
            <p>{a.detail}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
