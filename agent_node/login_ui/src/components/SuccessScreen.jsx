export default function SuccessScreen({ username, onLogout }) {
  return (
    <div style={s.wrapper}>
      <div style={s.card}>
        <h1 style={s.title}>Welcome, {username}!</h1>
        <p style={s.msg}>
          Authentication successful. This session has been recorded by the
          HIDS audit service.
        </p>

        <div style={s.infoBox}>
          <Row label="User"   value={username} />
          <Row label="Status" value={<span style={{ color: '#56d364' }}>Authenticated</span>} />
          <Row label="Time"   value={new Date().toLocaleString()} />
        </div>

        <button onClick={onLogout} style={s.btn}>Log Out</button>
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
  wrapper: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '100%', padding: '1rem',
  },
  card: {
    background: '#161b22', border: '1px solid #238636',
    borderRadius: '14px', padding: '2.5rem',
    width: '100%', maxWidth: '420px', textAlign: 'center',
  },
  title: { fontSize: '1.6rem', fontWeight: '700', color: '#56d364', marginBottom: '0.75rem' },
  msg:   { fontSize: '0.9rem', color: '#8b949e', lineHeight: '1.5', marginBottom: '1.5rem' },
  infoBox: {
    background: '#0d1117', border: '1px solid #21262d',
    borderRadius: '8px', padding: '0.25rem 1rem',
    marginBottom: '1.5rem', textAlign: 'left',
  },
  btn: {
    background: '#21262d', border: '1px solid #30363d', borderRadius: '7px',
    padding: '0.7rem 1.5rem', fontSize: '0.95rem', fontWeight: '600',
    color: '#c9d1d9', cursor: 'pointer', width: '100%',
  },
}
