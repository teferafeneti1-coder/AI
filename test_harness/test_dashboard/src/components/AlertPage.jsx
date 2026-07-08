import { useState, useEffect } from 'react'

const SEVERITY_COLORS = {
  CRITICAL: { bg: '#4b1c1c', text: '#ff7b72', border: '#da3633' },
  HIGH:     { bg: '#3d1c1c', text: '#f85149', border: '#b91c1c' },
  MEDIUM:   { bg: '#3d2e00', text: '#e3b341', border: '#9e6a03' },
  LOW:      { bg: '#1f3038', text: '#79c0ff', border: '#1f6feb' },
}

export default function AlertPage({ alert, onLockAccount, onReset }) {
  const [confirmVisible, setConfirmVisible] = useState(false)
  const [pulse, setPulse] = useState(false)

  const colors = SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.HIGH

  // Pulse animation on mount
  useEffect(() => {
    const t = setInterval(() => setPulse(p => !p), 800)
    return () => clearInterval(t)
  }, [])

  const ts = new Date(alert.timestamp * 1000).toLocaleString()

  return (
    <>
      <div style={styles.card}>
        {/* Header */}
        <div style={{ ...styles.alertHeader, background: colors.bg, border: `1px solid ${colors.border}` }}>
          <span style={{ fontSize: '2rem', animation: pulse ? 'none' : undefined }}>🚨</span>
          <div>
            <div style={{ ...styles.alertTitle, color: colors.text }}>
              INTRUSION DETECTED
            </div>
            <div style={styles.alertSubtitle}>
              Brute-force attack triggered HIDS alert
            </div>
          </div>
          <span
            style={{
              ...styles.badge,
              background: colors.bg,
              color: colors.text,
              border: `1px solid ${colors.border}`,
            }}
          >
            {alert.severity}
          </span>
        </div>

        {/* Alert Details */}
        <div style={styles.detailsGrid}>
          <DetailRow label="Alert ID"   value={<code style={styles.mono}>{alert.alert_id.slice(0, 16)}…</code>} />
          <DetailRow label="Attack Type" value={<Tag>{alert.attack_type.replace('_', ' ')}</Tag>} />
          <DetailRow label="Target User" value={<strong style={{ color: '#f0f6fc' }}>{alert.username}</strong>} />
          <DetailRow label="Source IP"   value={alert.source_ip} />
          <DetailRow label="Failed Attempts" value={
            <span style={{ color: colors.text, fontWeight: '700', fontSize: '1.1rem' }}>
              {alert.failed_attempts}
            </span>
          } />
          <DetailRow label="Timestamp"  value={<span style={{ color: '#8b949e', fontSize: '0.88rem' }}>{ts}</span>} />
        </div>

        {/* Description */}
        <div style={styles.descBox}>
          <div style={styles.descLabel}>Description</div>
          <div style={styles.descText}>{alert.description}</div>
        </div>

        {/* Actions */}
        <div style={styles.actionsTitle}>Recommended Actions</div>
        <div style={styles.actions}>
          <ActionBtn color="#21262d" border="#30363d" onClick={onReset}>
            👁 Ignore &amp; Reset
          </ActionBtn>
          <ActionBtn color="#1f6feb" onClick={() => setConfirmVisible(true)}>
            🔒 Lock Account
          </ActionBtn>
        </div>
      </div>

      {/* Confirm Modal */}
      {confirmVisible && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <div style={styles.modalIcon}>⚠️</div>
            <h3 style={styles.modalTitle}>Confirm: Lock Account</h3>
            <p style={styles.modalBody}>
              This will disable account <strong style={{ color: '#f0f6fc' }}>{alert.username}</strong> on
              the target machine. The user will not be able to log in until the account is re-enabled.
            </p>
            <div style={styles.modalActions}>
              <ActionBtn color="#21262d" border="#30363d" onClick={() => setConfirmVisible(false)}>
                Cancel
              </ActionBtn>
              <ActionBtn color="#da3633" onClick={() => { setConfirmVisible(false); onLockAccount() }}>
                Confirm Lock
              </ActionBtn>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function DetailRow({ label, value }) {
  return (
    <>
      <dt style={{ color: '#8b949e', fontSize: '0.85rem', fontWeight: '500', padding: '0.4rem 0' }}>
        {label}
      </dt>
      <dd style={{ padding: '0.4rem 0' }}>{value}</dd>
    </>
  )
}

function Tag({ children }) {
  return (
    <span style={{
      background: '#21262d', border: '1px solid #30363d',
      borderRadius: '4px', padding: '0.15rem 0.5rem',
      fontSize: '0.82rem', fontFamily: 'monospace', color: '#c9d1d9',
    }}>
      {children}
    </span>
  )
}

function ActionBtn({ color, border, children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: color,
        border: `1px solid ${border || color}`,
        borderRadius: '6px',
        padding: '0.6rem 1.1rem',
        fontSize: '0.9rem',
        fontWeight: '600',
        color: '#fff',
        cursor: 'pointer',
        flex: 1,
      }}
    >
      {children}
    </button>
  )
}

const styles = {
  card: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '12px',
    overflow: 'hidden',
    width: '100%',
  },
  alertHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1.25rem 1.5rem',
    borderRadius: '12px 12px 0 0',
    borderBottom: 'none',
  },
  alertTitle: {
    fontSize: '1.1rem',
    fontWeight: '800',
    letterSpacing: '0.06em',
  },
  alertSubtitle: {
    fontSize: '0.82rem',
    color: '#8b949e',
    marginTop: '0.2rem',
  },
  badge: {
    marginLeft: 'auto',
    padding: '0.3rem 0.7rem',
    borderRadius: '4px',
    fontSize: '0.8rem',
    fontWeight: '700',
    letterSpacing: '0.05em',
    whiteSpace: 'nowrap',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'auto 1fr',
    gap: '0 1.5rem',
    padding: '1.25rem 1.5rem',
    borderBottom: '1px solid #21262d',
  },
  descBox: {
    padding: '1rem 1.5rem',
    background: '#1c2128',
    borderBottom: '1px solid #21262d',
  },
  descLabel: {
    fontSize: '0.78rem',
    fontWeight: '600',
    color: '#8b949e',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: '0.4rem',
  },
  descText: {
    fontSize: '0.88rem',
    color: '#c9d1d9',
    lineHeight: '1.5',
  },
  actionsTitle: {
    fontSize: '0.78rem',
    fontWeight: '600',
    color: '#8b949e',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    padding: '1rem 1.5rem 0.5rem',
  },
  actions: {
    display: 'flex',
    gap: '0.75rem',
    padding: '0 1.5rem 1.5rem',
  },
  mono: {
    fontFamily: 'monospace',
    fontSize: '0.82rem',
    color: '#79c0ff',
    background: '#21262d',
    padding: '0.1rem 0.35rem',
    borderRadius: '3px',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.75)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  modal: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '12px',
    padding: '2rem',
    maxWidth: '400px',
    width: '90%',
    textAlign: 'center',
  },
  modalIcon: {
    fontSize: '2.5rem',
    marginBottom: '0.75rem',
  },
  modalTitle: {
    fontSize: '1.1rem',
    fontWeight: '700',
    color: '#f0f6fc',
    marginBottom: '0.75rem',
  },
  modalBody: {
    fontSize: '0.9rem',
    color: '#c9d1d9',
    lineHeight: '1.5',
    marginBottom: '1.5rem',
  },
  modalActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'center',
  },
}
