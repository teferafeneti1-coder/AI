import { useState } from 'react'
import LoginForm from './components/LoginForm'
import SuccessScreen from './components/SuccessScreen'
import AlertScreen from './components/AlertScreen'
import LockedScreen from './components/LockedScreen'

const MAX_ATTEMPTS = 5

export default function App() {
  const [screen, setScreen]       = useState('login')   // login | success | alert | locked
  const [failCount, setFailCount] = useState(0)
  const [lastUser, setLastUser]   = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')        // inline error on form

  async function handleSubmit(username, password) {
    setLoading(true)
    setError('')
    setLastUser(username)

    try {
      const res = await fetch('/api/login', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password }),
      })
      const data = await res.json()

      if (res.ok && data.success) {
        // ── Correct credentials ──────────────────────────────────────────
        setFailCount(0)
        setScreen('success')
      } else {
        // ── Wrong credentials ────────────────────────────────────────────
        const next = failCount + 1
        setFailCount(next)
        setError(data.message || 'Invalid credentials')

        if (next >= MAX_ATTEMPTS) {
          setScreen('alert')        // threshold hit → HIDS alert fired upstream
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
  }

  function handleLock() {
    setScreen('locked')
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
        />
      )}
      {screen === 'success' && (
        <SuccessScreen username={lastUser} onLogout={handleReset} />
      )}
      {screen === 'alert' && (
        <AlertScreen
          username={lastUser}
          failCount={failCount}
          onLock={handleLock}
          onDismiss={handleReset}
        />
      )}
      {screen === 'locked' && (
        <LockedScreen username={lastUser} onReset={handleReset} />
      )}
    </>
  )
}
