/**
 * AlertScreen — shown on the login page after 5 failed attempts.
 *
 * DISPLAY ONLY — no administrative action buttons.
 * The monitored user must never be able to lock/unlock their own account.
 * All response actions (lock, disconnect, shutdown) are available only
 * to the HIDS administrator on the HIDS dashboard (hids_node, port 5000).
 */
export default function AlertScreen({ username, failCount }) {
  return (
    <div style={s.wrapper}>
      <div style={s.card}>

        {/* Alert header */}
        <div style={s.alertHeader}>
          <div>
            <div style={s.alertTitle}>INTRUSION DETECTED</div>
            <div style={s.alertSub}>
              Brute-force attack — alert forwarded to HIDS administrator
            </div>
          </div>
          <span style={s.badge}>HIGH</span>
        </div>

        {/* Details */}
        <dl style={s.grid}>
          <dt style={s.dt}>Attack Type</dt>
          <dd style={s.dd}><code style={s.code}>brute_force</code></dd>

          <dt style={s.dt}>Username</dt>
          <dd style={s.dd}><strong style={{ color: '#f0f6fc' }}>{username}</strong></dd>

          <dt style={s.dt}>Failed Attempts</dt>
          <dd style={s.dd}>
            <span style={{ color: '#f85149', fontWeight: '700', fontSize: '1.1rem' }}>
              {failCount}
            </span>
          </dd>

          <dt style={s.dt}>Time</dt>
          <dd style={s.dd}>
            <span style={{ color: '#8b949e', fontSize: '0.85rem' }}>
              {new Date().toLocaleString()}
            </span>
          </dd>
        </dl>

        {/* Description */}
        <div style={s.descBox}>
          <div style={s.descLabel}>What happens next</div>
          <div style={s.descText}>
            {failCount} consecutive failed login attempts for "{username}" have been
            recorded and forwarded to the HIDS Analysis Server. The HIDS administrator
            has been notified and may take action on this machine remotely.
          </div>
        </div>

        {/* Status notice — no buttons */}
        <div style={s.notice}>
          Access to this account may be restricted by the administrator.
          Contact your system administrator if you believe this is an error.
        </div>

      </div>
    </div>
  )
}

const s = {
  wrapper: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '100%', padding: '1rem',
  },
  card: {
    background: '#161b22', border: '1px solid #30363d',
    borderRadius: '14px', overflow: 'hidden',
    width: '100%', maxWidth: '460px',
  },
  alertHeader: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '1.25rem 1.5rem',
    background: '#3d1c1c', borderBottom: '1px solid #b91c1c',
  },
  alertTitle: { fontSize: '1rem', fontWeight: '800', color: '#f85149', letterSpacing: '0.05em' },
  alertSub:   { fontSize: '0.78rem', color: '#8b949e', marginTop: '0.2rem' },
  badge: {
    background: '#4b1c1c', border: '1px solid #da3633', borderRadius: '4px',
    padding: '0.25rem 0.65rem', fontSize: '0.8rem', fontWeight: '700',
    color: '#f85149', whiteSpace: 'nowrap', flexShrink: 0,
  },
  grid: {
    display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0 1.5rem',
    padding: '1.25rem 1.5rem', borderBottom: '1px solid #21262d',
  },
  dt: { color: '#8b949e', fontSize: '0.83rem', fontWeight: '500', padding: '0.4rem 0' },
  dd: { padding: '0.4rem 0' },
  code: {
    fontFamily: 'monospace', fontSize: '0.82rem',
    background: '#21262d', padding: '0.1rem 0.4rem',
    borderRadius: '3px', color: '#79c0ff',
  },
  descBox: { padding: '1rem 1.5rem', background: '#1c2128', borderBottom: '1px solid #21262d' },
  descLabel: {
    fontSize: '0.73rem', fontWeight: '600', color: '#8b949e',
    textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.4rem',
  },
  descText: { fontSize: '0.86rem', color: '#c9d1d9', lineHeight: '1.5' },
  notice: {
    padding: '1rem 1.5rem',
    fontSize: '0.83rem', color: '#8b949e',
    lineHeight: '1.5', fontStyle: 'italic',
  },
}
