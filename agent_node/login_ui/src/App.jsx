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

  // Called when LoginForm's /api/account-status poll detects a server-side lock.
  // This is the ONLY path to LockedScreen — set by the HIDS admin, not the user.
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
        // Account was locked by the HIDS admin while the user was typing
        setLockReason(data.message || 'Account locked by administrator.')
        setScreen('locked')

      } else if (res.ok && data.success) {
        // Correct credentials
        setFailCount(0)
        setScreen('success')

      } else {
        // Wrong credentials — increment counter, show alert screen at threshold
        const next = failCount + 1
        setFailCount(next)
        setError(data.message || 'Invalid credentials')
        if (next >= MAX_ATTEMPTS) {
          // Show alert screen (display only — no action buttons)
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

      {/* AlertScreen is display-only — no admin action buttons */}
      {screen === 'alert' && (
        <AlertScreen username={lastUser} failCount={failCount} />
      )}

      {/* LockedScreen — only reachable via HIDS admin action or HTTP 423 from server */}
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
