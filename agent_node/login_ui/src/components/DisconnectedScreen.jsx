/**
 * DisconnectedScreen
 *
 * Shown on the agent's login page when the HIDS administrator has sent
 * a "Disconnect Network" command. This page is rendered BEFORE the network
 * adapter is physically disabled, giving the user a clear, informational
 * block page while there is still a brief window of connectivity.
 *
 * No action buttons — the user cannot retry, reconnect, or dismiss this.
 */
export default function DisconnectedScreen({ username, timestamp }) {
  const timeStr = timestamp
    ? new Date(timestamp * 1000).toLocaleString()
    : new Date().toLocaleString()

  return (
    <div style={s.page}>
      <div style={s.card}>

        {/* Severity stripe at top */}
        <div style={s.stripe} />

        <div style={s.body}>
          <div style={s.iconRow}>
            <div style={s.iconBox}>N</div>
          </div>

          <h1 style={s.heading}>Network Access Revoked</h1>

          <p style={s.message}>
            Your device has been disconnected from the network by the system
            administrator due to suspicious activity detected on this machine.
          </p>

          <div style={s.detailBox}>
            {username && (
              <Row label="Account"    value={username} />
            )}
            <Row label="Action"     value="Network Disconnect" />
            <Row label="Authorised by" value="HIDS Administrator" />
            <Row label="Time"       value={timeStr} />
          </div>

          <p style={s.contact}>
            Contact your system administrator to restore network access.
          </p>
        </div>

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
  page: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '100%', minHeight: '100vh', padding: '1rem',
    background: '#0d1117',
  },
  card: {
    background: '#161b22',
    border: '1px solid #6e40c9',
    borderRadius: '14px',
    overflow: 'hidden',
    width: '100%',
    maxWidth: '460px',
  },
  stripe: {
    height: '4px',
    background: 'linear-gradient(90deg, #6e40c9, #9161e0)',
  },
  body: {
    padding: '2rem 2.5rem 2.5rem',
    textAlign: 'center',
  },
  iconRow: {
    marginBottom: '1.25rem',
  },
  iconBox: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '52px',
    height: '52px',
    borderRadius: '50%',
    background: '#2d1f4e',
    border: '2px solid #6e40c9',
    fontSize: '1.4rem',
    fontWeight: '900',
    color: '#9161e0',
    letterSpacing: '-0.02em',
  },
  heading: {
    fontSize: '1.5rem',
    fontWeight: '800',
    color: '#c084fc',
    marginBottom: '0.9rem',
    letterSpacing: '0.02em',
  },
  message: {
    fontSize: '0.92rem',
    color: '#c9d1d9',
    lineHeight: '1.65',
    marginBottom: '1.75rem',
  },
  detailBox: {
    background: '#0d1117',
    border: '1px solid #21262d',
    borderRadius: '8px',
    padding: '0.25rem 1rem',
    marginBottom: '1.5rem',
    textAlign: 'left',
  },
  contact: {
    fontSize: '0.82rem',
    color: '#8b949e',
    lineHeight: '1.4',
    padding: '0.65rem 0.75rem',
    background: '#1a1a2e',
    border: '1px solid #2d1f4e',
    borderRadius: '6px',
  },
}
