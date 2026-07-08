import { useState } from 'react'

export default function LoginPage({ onLogin, failCount, maxAttempts }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    onLogin(username.trim(), password.trim())
    setPassword('')
  }

  const remaining = maxAttempts - failCount

  return (
    <div style={styles.card}>
      <div style={styles.iconBox}>🔐</div>
      <h1 style={styles.title}>HIDS Test Login</h1>
      <p style={styles.subtitle}>
        Test credentials: <code style={styles.code}>insa / 1234</code>
      </p>

      {failCount > 0 && failCount < maxAttempts && (
        <div style={styles.warningBanner}>
          <span style={styles.warningIcon}>⚠️</span>
          <div>
            <div style={styles.warningText}>
              {failCount} failed attempt{failCount > 1 ? 's' : ''}
            </div>
            <div style={styles.warningSubtext}>
              {remaining} attempt{remaining !== 1 ? 's' : ''} remaining before alert
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.field}>
          <label style={styles.label}>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
            placeholder="Enter username"
            autoFocus
          />
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            placeholder="Enter password"
          />
        </div>

        <button type="submit" style={styles.button}>
          Sign In
        </button>
      </form>

      <div style={styles.hint}>
        <p style={styles.hintText}>
          💡 Enter incorrect credentials {maxAttempts}× to trigger a HIGH-severity brute-force alert
        </p>
      </div>
    </div>
  )
}

const styles = {
  card: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '12px',
    padding: '2.5rem',
    width: '100%',
  },
  iconBox: {
    fontSize: '3rem',
    textAlign: 'center',
    marginBottom: '1rem',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: '700',
    textAlign: 'center',
    color: '#f0f6fc',
    marginBottom: '0.5rem',
  },
  subtitle: {
    fontSize: '0.9rem',
    textAlign: 'center',
    color: '#8b949e',
    marginBottom: '1.5rem',
  },
  code: {
    background: '#21262d',
    padding: '0.15rem 0.4rem',
    borderRadius: '4px',
    fontFamily: 'monospace',
    color: '#79c0ff',
  },
  warningBanner: {
    background: '#3d1c1c',
    border: '1px solid #b91c1c',
    borderRadius: '8px',
    padding: '0.75rem 1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '1.5rem',
  },
  warningIcon: {
    fontSize: '1.5rem',
  },
  warningText: {
    color: '#f85149',
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  warningSubtext: {
    color: '#e3b341',
    fontSize: '0.8rem',
    marginTop: '0.15rem',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.25rem',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.88rem',
    fontWeight: '600',
    color: '#c9d1d9',
  },
  input: {
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '6px',
    padding: '0.65rem 0.85rem',
    fontSize: '0.95rem',
    color: '#c9d1d9',
    outline: 'none',
    transition: 'border-color 0.15s',
  },
  button: {
    background: '#238636',
    border: 'none',
    borderRadius: '6px',
    padding: '0.75rem',
    fontSize: '1rem',
    fontWeight: '600',
    color: '#fff',
    cursor: 'pointer',
    transition: 'opacity 0.15s',
    marginTop: '0.5rem',
  },
  hint: {
    marginTop: '1.5rem',
    padding: '0.75rem',
    background: '#1f3038',
    border: '1px solid #1f6feb',
    borderRadius: '6px',
  },
  hintText: {
    fontSize: '0.82rem',
    color: '#79c0ff',
    lineHeight: '1.4',
  },
}
