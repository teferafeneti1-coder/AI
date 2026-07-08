export default function LockedScreen({ username, onReset }) {
  return (
    <div style={s.wrapper}>
      <div style={s.card}>
        <div style={s.icon}>🔒</div>
        <h1 style={s.title}>Account Locked</h1>
        <p style={s.msg}>
          Account <code style={s.code}>{username}</code> has been locked by the
          HIDS response system due to repeated failed login attempts.
        </p>

        <div style={s.infoBox}>
          <Row label="Account" value={username} />
          <Row label="Status"  value={<span style={{ color: '#f85149' }}>● Disabled</span>} />
          <Row label="Action"  value="Lock Account (HIDS Response)" />
          <Row label="Time"    value={new Date().toLocaleString()} />
        </div>

        <p style={s.note}>
          ℹ️ An administrator must re-enable this account to restore access.
        </p>

        <button onClick={onReset} style={s.btn}>Reset Test Session</button>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between',
                  padding: '0.5rem 0', borderBottom: '1px solid #21262d' }}>
      <span style={{ color: '#8b949e', fontSize: '0.85rem' }}>{label}</span>
      <span style={{ color: '#f0f6fc', fontSize: '0.88rem', fontWeight: '500' }}>{value}</span>
    </div>
  )
}

const s = {
  wrapper: { display: 'flex', alignItems: 'center', justifyContent: 'center',
             width: '100%', padding: '1rem' },
  card: {
    background: '#161b22',
    border: '1px solid #b91c1c',
    borderRadius: '14px',
    padding: '2.5rem',
    width: '100%',
    maxWidth: '420px',
    textAlign: 'center',
  },
  icon:  { fontSize: '3.5rem', marginBottom: '1rem' },
  title: { fontSize: '1.6rem', fontWeight: '700', color: '#f85149', marginBottom: '0.75rem' },
  msg:   { fontSize: '0.9rem', color: '#c9d1d9', lineHeight: '1.5', marginBottom: '1.5rem' },
  code: {
    background: '#21262d', padding: '0.15rem 0.4rem',
    borderRadius: '4px', fontFamily: 'monospace', color: '#79c0ff',
  },
  infoBox: {
    background: '#0d1117', border: '1px solid #21262d',
    borderRadius: '8px', padding: '0.25rem 1rem',
    marginBottom: '1.25rem', textAlign: 'left',
  },
  note: {
    fontSize: '0.82rem', color: '#79c0ff', lineHeight: '1.4',
    padding: '0.65rem 0.75rem',
    background: '#1f3038', border: '1px solid #1f6feb',
    borderRadius: '6px', marginBottom: '1.5rem',
  },
  btn: {
    background: '#238636', border: 'none', borderRadius: '7px',
    padding: '0.75rem', fontSize: '0.95rem', fontWeight: '600',
    color: '#fff', cursor: 'pointer', width: '100%',
  },
}
