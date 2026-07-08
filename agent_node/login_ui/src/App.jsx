import { useState, useCallback } from 'react'
import LoginForm from './components/LoginForm'
import SuccessScreen from './components/SuccessScreen'
import AlertScreen from './components/AlertScreen'
import LockedScreen from './components/LockedScreen'

const MAX_ATTEMPTS = 5

export default function App() {
  const [screen, setScreen]         = useState('login')
  const [failCount, setFailCount]   = useState(0)
  const [lastUser, setLastUser]     = useState('')
  const [lockReason, setLockReason] = useState('')
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')

  // ── Called when LoginForm's poll detects server-side lock ─────────────────
  const handleLockedByHIDS = useCallback((username, reason) => {
    setLastUser(username)
    setLockReason(reason || 'This account has been locked by the HIDS administrator.')
    setScreen('locked')
  }, [])

  async function handleSubmit(username, password) {
    setLoading(true)
    setError('')
    setLastUser(username)

    try {
      const res  = await fetch('/api/login', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password }),
      })
      const data = await res.json()

      if (res.status === 423 || data.locked) {
        // ── Account was locked by HIDS while user was trying ──────────────
        setLockReason(data.message || 'Account locked by administrator.')
        setScreen('locked')

      } else if (res.ok && data.success) {
        // ── Correct credentials ────────────────────────────────────────────
        setFailCount(0)
        setScreen('success')

      } else {
        // ── Wrong credentials ──────────────────────────────────────────────
        const next = failCount + 1
        setFailCount(next)
        setError(data.message || 'Invalid credentials')
        if (next >= MAX_ATTEMPTS) {
          setScreen('alert')
        }
      }
    } catch {
      setError('Could not reach server. Try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setScreen('login')
    setFailCount(0)
    setError('')
    setLastUser('')
    setLockReason('')
  }

  return (
    <>
      {screen === 'login' && (
        <LoginForm
          onSubmit={handleSubmit}
          failCount={failCount}
          maxAttempts={MAX_ATTEMPTS}
          loading={loading}
          error={error}
          onLocked={handleLockedByHIDS}
        />
      )}

      {screen === 'success' && (
        <SuccessScreen username={lastUser} onLogout={handleReset} />
      )}

      {screen === 'alert' && (
        <AlertScreen
          username={lastUser}
          failCount={failCount}
          onLock={() => setScreen('locked')}
          onDismiss={handleReset}
        />
      )}

      {/* LockedScreen is shown in two cases:
          1. Admin clicks Lock Account on HIDS dashboard (polled / HTTP 423)
          2. User clicks Lock Account locally on AlertScreen             */}
      {screen === 'locked' && (
        <LockedScreen
          username={lastUser}
          reason={lockReason}
          onReset={handleReset}
        />
      )}
    </>
  )
}
