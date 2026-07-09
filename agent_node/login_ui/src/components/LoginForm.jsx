import { useState, useEffect, useRef } from 'react'

export default function LoginForm({ onSubmit, failCount, maxAttempts, loading, error, onLocked }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [shake, setShake]       = useState(false)
  const usernameRef             = useRef(null)

  // Shake form on every new error
  useEffect(() => {
    if (error) {
      setShake(true)
      const t = setTimeout(() => setShake(false), 400)
      return () => clearTimeout(t)
    }
  }, [error, failCount])

  // Auto-focus username on mount
  useEffect(() => { usernameRef.current?.focus() }, [])

  // Poll /api/account-status every 2 s while username is typed.
  // The moment admin clicks Lock Account on the HIDS dashboard,
  // login_api sets _account_locked = True in Supabase and in-memory.
  // This poll catches it within 2 s and switches the UI to LockedScreen.
  useEffect(() => {
    if (!username) return
    const id = setInterval(async () => {
      try {
        const res  = await fetch(`/api/account-status?username=${encodeURIComponent(username)}`)
        const data = await res.json()
        if (data.locked) {
          clearInterval(id)
          onLocked(data.username || username, data.reason)
        }
      } catch { /* server unreachable — keep polling */ }
    }, 2000)
    return () => clearInterval(id)
  }, [username, onLocked])

  function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim() || loading) return
    onSubmit(username.trim(), password.trim())
    setPassword('')
  }

  const remaining = maxAttempts - failCount
  const nearLimit = failCount >= 3

  return (
    <div style={s.wrapper}>
      <div style={{
        ...s.card,
        animation:   shake ? 'shake 0.4s ease' : 'none',
        borderColor: failCount > 0 ? '#b91c1c' : '#30363d',
      }}>

        {/* Header — no emoji */}
        <div style={s.header}>
          <div style={s.logoMark}>HIDS</div>
          <div>
            <div style={s.brand}>SecureAccess</div>
            <div style={s.brandSub}>Host Intrusion Detection System</div>
          </div>
        </div>

        <h2 style={s.title}>Sign in to your account</h2>

        {/* Failure banner — no emoji */}
        {failCount > 0 && (
          <div style={{
            ...s.banner,
            background:  nearLimit ? '#3d0f0f' : '#2a1a1a',
            borderColor: nearLimit ? '#f85149' : '#b91c1c',
          }}>
            <div>
              <div style={{ ...s.bannerTitle, color: nearLimit ? '#f85149' : '#e3b341' }}>
                {error}
              </div>
              <div style={s.bannerSub}>
                {remaining} attempt{remaining !== 1 ? 's' : ''} remaining
                {nearLimit ? ' — account will be locked' : ''}
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={s.form}>
          <div style={s.field}>
            <label style={s.label} htmlFor="hids-username">Username</label>
            <input
              id="hids-username"
              ref={usernameRef}
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              style={{ ...s.input, borderColor: failCount > 0 ? '#b91c1c' : '#30363d' }}
              placeholder="Enter username"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div style={s.field}>
            <label style={s.label} htmlFor="hids-password">Password</label>
            <input
              id="hids-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{ ...s.input, borderColor: failCount > 0 ? '#b91c1c' : '#30363d' }}
              placeholder="Enter password"
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {/* Attempt dots */}
          {failCount > 0 && (
            <div style={s.dots}>
              {Array.from({ length: maxAttempts }).map((_, i) => (
                <span key={i} style={{
                  ...s.dot,
                  background: i < failCount ? '#f85149' : '#21262d',
                  border:     i < failCount ? '1px solid #da3633' : '1px solid #30363d',
                }} />
              ))}
              <span style={s.dotsLabel}>{failCount}/{maxAttempts} attempts</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim() || !password.trim()}
            style={{
              ...s.btn,
              background: nearLimit ? '#b91c1c' : failCount > 0 ? '#9e2020' : '#238636',
              opacity: loading ? 0.7 : 1,
              cursor:  loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

const s = {
  wrapper:  { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: '1rem' },
  card:     { background: '#161b22', border: '1px solid #30363d', borderRadius: '14px', padding: '2.5rem', width: '100%', maxWidth: '420px', transition: 'border-color 0.3s' },
  header:   { display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.75rem' },
  logoMark: { background: '#1f6feb', color: '#fff', fontWeight: '800', fontSize: '0.75rem', letterSpacing: '0.05em', padding: '0.35rem 0.55rem', borderRadius: '6px', flexShrink: 0 },
  brand:    { fontSize: '1.1rem', fontWeight: '800', color: '#f0f6fc', letterSpacing: '0.02em' },
  brandSub: { fontSize: '0.72rem', color: '#8b949e', marginTop: '0.1rem' },
  title:    { fontSize: '1.25rem', fontWeight: '700', color: '#f0f6fc', marginBottom: '1.5rem' },
  banner:   { border: '1px solid', borderRadius: '8px', padding: '0.75rem 1rem', marginBottom: '1.25rem', animation: 'fadeIn 0.2s ease' },
  bannerTitle: { fontWeight: '600', fontSize: '0.88rem' },
  bannerSub:   { color: '#8b949e', fontSize: '0.78rem', marginTop: '0.2rem' },
  form:  { display: 'flex', flexDirection: 'column', gap: '1.1rem' },
  field: { display: 'flex', flexDirection: 'column', gap: '0.45rem' },
  label: { fontSize: '0.87rem', fontWeight: '600', color: '#c9d1d9' },
  input: { background: '#0d1117', border: '1px solid #30363d', borderRadius: '7px', padding: '0.7rem 0.9rem', fontSize: '0.95rem', color: '#f0f6fc', outline: 'none', width: '100%', transition: 'border-color 0.2s' },
  dots:      { display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '-0.2rem' },
  dot:       { width: '10px', height: '10px', borderRadius: '50%', display: 'inline-block', transition: 'background 0.25s' },
  dotsLabel: { fontSize: '0.75rem', color: '#8b949e', marginLeft: '0.2rem' },
  btn:       { border: 'none', borderRadius: '7px', padding: '0.78rem', fontSize: '1rem', fontWeight: '700', color: '#fff', transition: 'background 0.3s', letterSpacing: '0.02em', marginTop: '0.2rem' },
}
