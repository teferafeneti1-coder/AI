export default function AttemptLog({ attempts, failCount, maxAttempts }) {
  const percentage = Math.min((failCount / maxAttempts) * 100, 100)
  const color = failCount >= maxAttempts ? '#f85149' : failCount >= maxAttempts * 0.6 ? '#e3b341' : '#56d364'

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Attempt Log</h2>

      {/* Progress bar */}
      <div style={styles.progressBox}>
        <div style={styles.progressLabel}>
          <span>Failed Attempts</span>
          <span style={{ fontWeight: '700', color }}>{failCount} / {maxAttempts}</span>
        </div>
        <div style={styles.progressTrack}>
          <div style={{ ...styles.progressFill, width: `${percentage}%`, background: color }} />
        </div>
      </div>

      {/* Attempt list */}
      <div style={styles.logList}>
        {attempts.length === 0 ? (
          <div style={styles.empty}>No attempts yet</div>
        ) : (
          attempts.map((a) => (
            <div
              key={a.id}
              style={{
                ...styles.logItem,
                borderLeft: `3px solid ${a.status === 'success' ? '#56d364' : '#f85149'}`,
              }}
            >
              <div style={styles.logHeader}>
                <span style={{
                  ...styles.logIcon,
                  color: a.status === 'success' ? '#56d364' : '#f85149',
                }}>
                  {a.status === 'success' ? '✓' : '✗'}
                </span>
                <span style={styles.logUsername}>{a.username}</span>
                <span style={styles.logTime}>{a.time}</span>
              </div>
              <div style={{
                ...styles.logStatus,
                color: a.status === 'success' ? '#56d364' : '#f85149',
              }}>
                {a.status === 'success' ? 'Success' : 'Failed'}
              </div>
              <div style={styles.logMessage}>{a.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const styles = {
  panel: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '12px',
    padding: '1.5rem',
    width: '340px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
  },
  heading: {
    fontSize: '1rem',
    fontWeight: '700',
    color: '#f0f6fc',
    marginBottom: '1rem',
    letterSpacing: '0.03em',
  },
  progressBox: {
    marginBottom: '1.5rem',
  },
  progressLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.82rem',
    color: '#8b949e',
    marginBottom: '0.5rem',
  },
  progressTrack: {
    background: '#21262d',
    borderRadius: '8px',
    height: '8px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.3s ease, background 0.3s ease',
    borderRadius: '8px',
  },
  logList: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  empty: {
    textAlign: 'center',
    color: '#8b949e',
    fontSize: '0.85rem',
    padding: '2rem 0',
  },
  logItem: {
    background: '#0d1117',
    border: '1px solid #21262d',
    borderRadius: '6px',
    padding: '0.75rem',
    fontSize: '0.82rem',
  },
  logHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.4rem',
  },
  logIcon: {
    fontSize: '1rem',
    fontWeight: '700',
  },
  logUsername: {
    fontWeight: '600',
    color: '#c9d1d9',
    flex: 1,
  },
  logTime: {
    fontSize: '0.75rem',
    color: '#8b949e',
  },
  logStatus: {
    fontSize: '0.8rem',
    fontWeight: '600',
    marginBottom: '0.25rem',
  },
  logMessage: {
    color: '#8b949e',
    fontSize: '0.78rem',
    lineHeight: '1.3',
  },
}
