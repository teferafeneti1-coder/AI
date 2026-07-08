export default function SuccessPage({ username, onLogout }) {
  return (
    <div style={styles.card}>
      <div style={styles.iconBox}>✅</div>
      <h1 style={styles.title}>Welcome, {username}!</h1>
      <p style={styles.message}>Authentication successful. This session has been logged by the HIDS audit service.</p>
      <div style={styles.statusBox}>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Status</span>
          <span style={styles.statusValue}>
            <span style={{ color: '#56d364' }}>●</span> Authenticated
          </span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>User</span>
          <span style={styles.statusValue}>{username}</span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Login time</span>
          <span style={styles.statusValue}>{new Date().toLocaleString()}</span>
        </div>
      </div>
      <button onClick={onLogout} style={styles.button}>
        Log Out
      </button>
    </div>
  )
}

const styles = {
  card: {
    background: '#161b22',
    border: '1px solid #238636',
    borderRadius: '12px',
    padding: '2.5rem',
    textAlign: 'center',
    width: '100%',
  },
  iconBox: {
    fontSize: '4rem',
    marginBottom: '1rem',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: '700',
    color: '#56d364',
    marginBottom: '1rem',
  },
  message: {
    fontSize: '0.9rem',
    color: '#c9d1d9',
    lineHeight: '1.5',
    marginBottom: '1.5rem',
  },
  statusBox: {
    background: '#0d1117',
    border: '1px solid #21262d',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '1.5rem',
  },
  statusRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    borderBottom: '1px solid #21262d',
  },
  statusLabel: {
    fontSize: '0.85rem',
    color: '#8b949e',
  },
  statusValue: {
    fontSize: '0.88rem',
    color: '#f0f6fc',
    fontWeight: '500',
  },
  button: {
    background: '#21262d',
    border: '1px solid #30363d',
    borderRadius: '6px',
    padding: '0.75rem 1.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    color: '#c9d1d9',
    cursor: 'pointer',
    width: '100%',
  },
}
