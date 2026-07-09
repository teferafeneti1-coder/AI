import { useState } from 'react'

export default function AlertScreen({ username, failCount, onLock, onDismiss }) {
  const [confirmOpen, setConfirmOpen] = useState(false)

  return (
    <>
      <div style={s.wrapper}>
        <div style={s.card}>
          {/* Alert header */}
          <div style={s.alertHeader}>
            <div>
              <div style={s.alertTitle}>INTRUSION DETECTED</div>
              <div style={s.alertSub}>Brute-force attack — HIDS alert generated</div>
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
            <div style={s.descLabel}>Description</div>
            <div style={s.descText}>
              {failCount} consecutive failed login attempts for user "{username}".
              This event has been forwarded to the HIDS Analysis Server and the
              HIDS dashboard has been notified.
            </div>
          </div>

          {/* Actions */}
          <div style={s.actionsLabel}>Recommended Actions</div>
          <div style={s.actions}>
            <button style={{ ...s.btn, ...s.btnGray }} onClick={onDismiss}>
              Ignore and Reset
            </button>
            <button style={{ ...s.btn, ...s.btnRed }} onClick={() => setConfirmOpen(true)}>
              Lock Account
            </button>
          </div>
        </div>
      </div>

      {/* Confirm modal */}
      {confirmOpen && (
        <div style={s.overlay} onClick={() => setConfirmOpen(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <h3 style={s.modalTitle}>Confirm: Lock Account</h3>
            <p style={s.modalBody}>
              This will disable the account{' '}
              <strong style={{ color: '#f0f6fc' }}>{username}</strong> on this
              machine. The user cannot log in until an administrator re-enables it.
            </p>
            <div style={s.modalActions}>
              <button style={{ ...s.btn, ...s.btnGray }} onClick={() => setConfirmOpen(false)}>
                Cancel
              </button>
              <button
                style={{ ...s.btn, ...s.btnRed }}
                onClick={() => { setConfirmOpen(false); onLock() }}
              >
                Confirm Lock
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

const s = {
  wrapper: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: '1rem' },
  card: { background: '#161b22', border: '1px solid #30363d', borderRadius: '14px', overflow: 'hidden', width: '100%', maxWidth: '460px' },
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
    color: '#f85149', whiteSpace: 'nowrap',
  },
  grid: { display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0 1.5rem', padding: '1.25rem 1.5rem', borderBottom: '1px solid #21262d' },
  dt: { color: '#8b949e', fontSize: '0.83rem', fontWeight: '500', padding: '0.4rem 0' },
  dd: { padding: '0.4rem 0' },
  code: { fontFamily: 'monospace', fontSize: '0.82rem', background: '#21262d', padding: '0.1rem 0.4rem', borderRadius: '3px', color: '#79c0ff' },
  descBox: { padding: '1rem 1.5rem', background: '#1c2128', borderBottom: '1px solid #21262d' },
  descLabel: { fontSize: '0.73rem', fontWeight: '600', color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.4rem' },
  descText: { fontSize: '0.86rem', color: '#c9d1d9', lineHeight: '1.5' },
  actionsLabel: { fontSize: '0.73rem', fontWeight: '600', color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '1rem 1.5rem 0.5rem' },
  actions: { display: 'flex', gap: '0.75rem', padding: '0 1.5rem 1.5rem' },
  btn: { flex: 1, border: 'none', borderRadius: '6px', padding: '0.65rem 0.75rem', fontSize: '0.9rem', fontWeight: '600', color: '#fff', cursor: 'pointer' },
  btnGray: { background: '#21262d', border: '1px solid #30363d', color: '#c9d1d9' },
  btnRed:  { background: '#da3633' },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modal: { background: '#161b22', border: '1px solid #30363d', borderRadius: '12px', padding: '2rem', maxWidth: '380px', width: '90%' },
  modalTitle: { fontSize: '1.1rem', fontWeight: '700', color: '#f85149', marginBottom: '0.75rem' },
  modalBody: { fontSize: '0.88rem', color: '#c9d1d9', lineHeight: '1.5', marginBottom: '1.5rem' },
  modalActions: { display: 'flex', gap: '0.75rem' },
}
