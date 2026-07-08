export default function LockedPage({ username, onReset }) {
  return (
    <div style={styles.card}>
      <div style={styles.iconBox}>🔒</div>
      <h1 style={styles.title}>Account Locked</h1>
      <p style={styles.message}>
        User account <code style={styles.code}>{username}</code> has been successfully locked by the HIDS response system.
      </p>
      <div style={styles.statusBox}>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Status</span>
          <span style={styles.statusValue}>
            <span style={{ color: '#f85149' }}>●</span> Disabled
          </span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Action</span>
          <span style={styles.statusValue}>Account Lock</span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Timestamp</span>
          <span style={styles.statusValue}>{new Date().toLocaleString()}</span>
        </div>
      </div>
      <p style={styles.note}>
        ℹ️ In a production environment, the user would need administrative intervention to re-enable their account.
      </p>
      <button onClick={onReset} style={styles.button}>
        Reset Test Session
      </button>
    </div>
  )
}

const styles = {
  card: {
    background: '#161b22',
    border: '1px solid #30363d',
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
    color: '#f85149',
    marginBottom: '1rem',
  },
  message: {
    fontSize: '0.95rem',
    color: '#c9d1d9',
    lineHeight: '1.6',
    marginBottom: '1.5rem',
  },
  code: {
    background: '#21262d',
    padding: '0.15rem 0.4rem',
    borderRadius: '4px',
    fontFamily: 'monospace',
    color: '#79c0ff',
    fontWeight: '600',
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
  note: {
    fontSize: '0.82rem',
    color: '#8b949e',
    lineHeight: '1.5',
    padding: '0.75rem',
    background: '#1f3038',
    border: '1px solid #1f6feb',
    borderRadius: '6px',
    marginBottom: '1.5rem',
  },
  button: {
    background: '#238636',
    border: 'none',
    borderRadius: '6px',
    padding: '0.75rem 1.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    color: '#fff',
    cursor: 'pointer',
    width: '100%',
  },
}
