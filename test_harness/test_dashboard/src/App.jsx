import { useState, useCallback } from 'react'
import LoginPage from './components/LoginPage'
import AlertPage from './components/AlertPage'
import LockedPage from './components/LockedPage'
import SuccessPage from './components/SuccessPage'
import AttemptLog from './components/AttemptLog'

// ── Test credentials ───────────────────────────────────────────────────────
const VALID_USER = 'insa'
const VALID_PASS = '1234'
const MAX_ATTEMPTS = 5
const SOURCE_IP = '192.168.1.100'  // simulated attacker IP

export default function App() {
  const [screen, setScreen] = useState('login')  // login | alert | locked | success
  const [failCount, setFailCount] = useState(0)
  const [attempts, setAttempts] = useState([])   // full attempt history
  const [alert, setAlert] = useState(null)
  const [lastUsername, setLastUsername] = useState('')

  // Send a simulated login event to the HIDS backend.
  // Falls back gracefully if backend is not running (pure UI demo still works).
  const sendEventToHIDS = useCallback(async (username, status) => {
    try {
      await fetch('/api/test/login-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          source_ip: SOURCE_IP,
          status,        // "success" | "fail"
        }),
      })
    } catch {
      // Backend not reachable — test dashboard still works standalone
    }
  }, [])

  const handleLogin = useCallback(async (username, password) => {
    const now = new Date()
    setLastUsername(username)

    if (username === VALID_USER && password === VALID_PASS) {
      // ── Correct credentials ──────────────────────────────────────────────
      const entry = {
        id: Date.now(),
        username,
        status: 'success',
        time: now.toLocaleTimeString(),
        message: 'Login successful',
      }
      setAttempts(prev => [entry, ...prev])
      await sendEventToHIDS(username, 'success')
      setScreen('success')
      return
    }

    // ── Wrong credentials ────────────────────────────────────────────────
    const newCount = failCount + 1
    const entry = {
      id: Date.now(),
      username,
      status: 'fail',
      time: now.toLocaleTimeString(),
      message: `Attempt ${newCount}/${MAX_ATTEMPTS} — invalid credentials`,
    }
    setAttempts(prev => [entry, ...prev])
    await sendEventToHIDS(username, 'fail')
    setFailCount(newCount)

    if (newCount >= MAX_ATTEMPTS) {
      // ── Threshold hit → trigger alert ────────────────────────────────
      const newAlert = {
        alert_id: crypto.randomUUID(),
        severity: 'HIGH',
        attack_type: 'brute_force',
        username,
        source_ip: SOURCE_IP,
        failed_attempts: newCount,
        timestamp: Math.floor(Date.now() / 1000),
        description: `${newCount} consecutive failed login attempts for user "${username}" from ${SOURCE_IP}.`,
      }
      setAlert(newAlert)
      setScreen('alert')
    }
  }, [failCount, sendEventToHIDS])

  const handleReset = useCallback(() => {
    setScreen('login')
    setFailCount(0)
    setAlert(null)
    setAttempts([])
    setLastUsername('')
  }, [])

  const handleLockAccount = useCallback(() => {
    setScreen('locked')
  }, [])

  const handleDismissSuccess = useCallback(() => {
    setScreen('login')
    setFailCount(0)
    setAttempts([])
    setLastUsername('')
  }, [])

  return (
    <div style={styles.root}>
      {/* ── Left panel: current screen ─── */}
      <div style={styles.mainPanel}>
        {screen === 'login' && (
          <LoginPage
            onLogin={handleLogin}
            failCount={failCount}
            maxAttempts={MAX_ATTEMPTS}
          />
        )}
        {screen === 'alert' && alert && (
          <AlertPage
            alert={alert}
            onLockAccount={handleLockAccount}
            onReset={handleReset}
          />
        )}
        {screen === 'locked' && (
          <LockedPage
            username={lastUsername}
            onReset={handleReset}
          />
        )}
        {screen === 'success' && (
          <SuccessPage
            username={lastUsername}
            onLogout={handleDismissSuccess}
          />
        )}
      </div>

      {/* ── Right panel: attempt log ─── */}
      <AttemptLog attempts={attempts} failCount={failCount} maxAttempts={MAX_ATTEMPTS} />
    </div>
  )
}

const styles = {
  root: {
    display: 'flex',
    gap: '2rem',
    padding: '2rem',
    width: '100%',
    maxWidth: '1100px',
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  mainPanel: {
    flex: '0 0 420px',
  },
}
