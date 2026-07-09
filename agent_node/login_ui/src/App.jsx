import { useState, useCallback, useEffect } from 'react'
import LoginForm from './components/LoginForm'
import SuccessScreen from './components/SuccessScreen'
import AlertScreen from './components/AlertScreen'
import LockedScreen from './components/LockedScreen'
import DisconnectedScreen from './components/DisconnectedScreen'

const MAX_ATTEMPTS = 5

export default function App() {
  const [screen, setScreen]           = useState('login')
  const [failCount, setFailCount]     = useState(0)
  const [lastUser, setLastUser]       = useState('')
  const [lockReason, setLockReason]   = useState('')
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState('')
  const [disconnectInfo, setDisconnectInfo] = useState({ username: '', timestamp: 0 })

  // ── Global machine-status poll (runs on EVERY screen) ────────────────────
  // executor.py calls set_machine_disconnected() BEFORE running netsh.
  // This poll catches that state change within 2 s and switches immediately
  // to DisconnectedScreen — before the network adapter is actually disabled.
  useEffect(() => {
    // Don't poll if already on the disconnected screen
    if (screen === 'disconnected') return

    const id = setInterval(async () => {
      try {
        const res  = await fetch('/api/machine-status')
        const data = await res.json()
        if (data.status === 'disconnected') {
          clearInterval(id)
          setDisconnectInfo({
            username:  data.username  || '',
            timestamp: data.timestamp || 0,
          })
          setScreen('disconnected')
        }
      } catch { /* server not reachable — keep polling until it is */ }
    }, 2000)

    return () => clearInterval(id)
  }, [screen])

  // ── Lock detected by account-status poll (LoginForm callback) ────────────
  const handleLockedByHIDS = useCallback((username, reason) => {
    setLastUser(username)
    setLockReason(reason || 'This account has been locked by the HIDS administrator.')
    setScreen('locked')
  }, [])

  // ── Login submit ──────────────────────────────────────────────────────────
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
        setLockReason(data.message || 'Account locked by administrator.')
        setScreen('locked')
      } else if (res.ok && data.success) {
        setFailCount(0)
        setScreen('success')
      } else {
        const next = failCount + 1
        setFailCount(next)
        setError(data.message || 'Invalid credentials')
        if (next >= MAX_ATTEMPTS) setScreen('alert')
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

  // ── Render ────────────────────────────────────────────────────────────────
  // DisconnectedScreen takes priority over everything else — it is set by
  // the global poll above and cannot be dismissed by the user.
  if (screen === 'disconnected') {
    return (
      <DisconnectedScreen
        username={disconnectInfo.username}
        timestamp={disconnectInfo.timestamp}
      />
    )
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

      {/* AlertScreen — display only, no admin action buttons */}
      {screen === 'alert' && (
        <AlertScreen username={lastUser} failCount={failCount} />
      )}

      {/* LockedScreen — only reachable via HIDS admin lock or HTTP 423 */}
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
