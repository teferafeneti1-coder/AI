import { useState } from 'react'

export default function LoginPage({ onLogin, failCount, maxAttempts }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [shake, setShake]       = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setErrorMsg('Please enter both username and password.')
      return
    }
    setErrorMsg('')
    onLogin(username.trim(), password.trim())
    setPassword('')

    // Trigger shake animation on wrong password (App tells us via failCount increasing)
    // We do it optimistically — App will update failCount after this call
    setShake(true)
    setTimeout(() => setShake(false), 500)
  }

  const remaining   = maxAttempts - failCount
  const nearLimit   = failCount >= 3 && failCount < maxAttempts
  const inputBorder = failCount > 0 ? '1px solid #b91c1c' : '1px solid #30363d'

  return (
    <div style={styles.card}>
      {/* Logo / Icon */}
      <div style={styles.logoRow}>
        <span style={styles.logoIcon}>🛡</span>
        <div>
          <div style={styles.appName}>SecureAccess</div>
          <div style={styles.appSub}>Host Intrusion Detection System</div>
        </div>
      </div>

      <h2 style={styles.title}>Sign in to your account</h2>

      {/* Wrong-password error banner — appears after 1st fail */}
      {failCount > 0 && (
        <div style={{
          ...styles.errorBanner,
          background: nearLimit ? '#3d1c1c' : '#2a1a1a',
          borderColor: nearLimit ? '#f85149' : '#b91c1c',
        }}>
          <span style={styles.errorIcon}>{nearLimit ? '🚨' : '⚠️'}</span>
          <div>
            <div style={styles.errorText}>
              Incorrect username or password.
            </div>
            <div style={styles.errorSub}>
              {remaining} attempt{remaining !== 1 ? 's' : ''} remaining
              {nearLimit ? ' — your account will be locked!' : '.'}
            </div>
          </div>
        </div>
      )}

      {/* Inline validation message */}
      {errorMsg && (
        <div style={styles.inlineError}>{errorMsg}</div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          ...styles.form,
          animation: shake ? 'shake 0.4s ease' : 'none',
        }}
      >
        <div style={styles.field}>
          <label style={styles.label} htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => { setUsername(e.target.value); setErrorMsg('') }}
            style={{ ...styles.input, borderColor: failCount > 0 ? '#b91c1c' : '#30363d' }}
            placeholder="Enter your username"
            autoComplete="username"
            autoFocus
          />
        </div>

        <div style={styles.field}>
          <label style={styles.label} htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setErrorMsg('') }}
            style={{ ...styles.input, borderColor: failCount > 0 ? '#b91c1c' : '#30363d' }}
            placeholder="Enter your password"
            autoComplete="current-password"
          />
        </div>

        {/* Attempt dots */}
        {failCount > 0 && (
          <div style={styles.dotsRow} aria-label={`${failCount} of ${maxAttempts} attempts used`}>
            {Array.from({ length: maxAttempts }).map((_, i) => (
              <span
                key={i}
                style={{
                  ...styles.dot,
                  background: i < failCount ? '#f85149' : '#21262d',
                  border: i < failCount ? '1px solid #da3633' : '1px solid #30363d',
                }}
              />
            ))}
            <span style={styles.dotsLabel}>{failCount}/{maxAttempts} failed</span>
          </div>
        )}

        <button
          type="submit"
          style={{
            ...styles.button,
            background: failCount >= maxAttempts - 1 ? '#b91c1c' : '#238636',
          }}
        >
          Sign In
        </button>
      </form>

      {/* Shake keyframe injected via style tag */}
      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20%       { transform: translateX(-8px); }
          40%       { transform: translateX(8px); }
          60%       { transform: translateX(-6px); }
          80%       { transform: translateX(6px); }
        }
      `}</style>
    </div>
  )
}

const styles = {
  card: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '14px',
    padding: '2.5rem',
    width: '100%',
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '1.75rem',
  },
  logoIcon: {
    fontSize: '2.4rem',
    lineHeight: 1,
  },
  appName: {
    fontSize: '1.15rem',
    fontWeight: '800',
    color: '#f0f6fc',
    letterSpacing: '0.02em',
  },
  appSub: {
    fontSize: '0.75rem',
    color: '#8b949e',
    marginTop: '0.1rem',
  },
  title: {
    fontSize: '1.3rem',
    fontWeight: '700',
    color: '#f0f6fc',
    marginBottom: '1.5rem',
  },
  errorBanner: {
    border: '1px solid',
    borderRadius: '8px',
    padding: '0.75rem 1rem',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.75rem',
    marginBottom: '1.25rem',
  },
  errorIcon: {
    fontSize: '1.25rem',
    marginTop: '0.05rem',
    flexShrink: 0,
  },
  errorText: {
    color: '#f85149',
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  errorSub: {
    color: '#e3b341',
    fontSize: '0.8rem',
    marginTop: '0.2rem',
  },
  inlineError: {
    color: '#f85149',
    fontSize: '0.82rem',
    marginBottom: '0.75rem',
    paddingLeft: '0.25rem',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.1rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.45rem',
  },
  label: {
    fontSize: '0.87rem',
    fontWeight: '600',
    color: '#c9d1d9',
  },
  input: {
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '7px',
    padding: '0.7rem 0.9rem',
    fontSize: '0.95rem',
    color: '#f0f6fc',
    outline: 'none',
    transition: 'border-color 0.2s',
    width: '100%',
  },
  dotsRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    marginTop: '0.1rem',
  },
  dot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    display: 'inline-block',
    transition: 'background 0.3s',
  },
  dotsLabel: {
    fontSize: '0.75rem',
    color: '#8b949e',
    marginLeft: '0.25rem',
  },
  button: {
    border: 'none',
    borderRadius: '7px',
    padding: '0.8rem',
    fontSize: '1rem',
    fontWeight: '700',
    color: '#fff',
    cursor: 'pointer',
    transition: 'background 0.3s, opacity 0.15s',
    marginTop: '0.25rem',
    letterSpacing: '0.02em',
  },
}
