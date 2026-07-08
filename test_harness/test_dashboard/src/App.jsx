import { useState, useCallback } from 'react'
import LoginPage from './components/LoginPage'
import AlertPage from './components/AlertPage'
import LockedPage from './components/LockedPage'
import SuccessPage from './components/SuccessPage'
import AttemptLog from './components/AttemptLog'

// ── Valid credentials (checked silently — user types freely) ──────────────
const VALID_USER = 'insa'
const VALID_PASS = '1234'
const MAX_ATTEMPTS = 5
const SOURCE_IP = '192.168.1.100'

export default function App() {
  const [screen, setScreen]         = useState('login')
  const [failCount, setFailCount]   = useState(0)
  const [attempts, setAttempts]     = useState([])
  const [alert, setAlert]           = useState(null)
  const [lastUsername, setLastUsername] = useState('')

  // Forward login event to HIDS backend (non-blocking, fails silently)
  const sendEventToHIDS = useCallback(async (username, status) => {
    try {
      await fetch('/api/test/login-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, source_ip: SOURCE_IP, status }),
      })
    } catch {
      // backend not running — UI still works standalone
    }
  }, [])

  const handleLogin = useCallback(async (username, password) => {
    const now = new Date()
    setLastUsername(username)

    // ── Correct credentials ─────────────────────────────────────────────
    if (username === VALID_USER && password === VALID_PASS) {
      setAttempts(prev => [{
        id: Date.now(),
        username,
        status: 'success',
        time: now.toLocaleTimeString(),
        message: 'Login successful',
      }, ...prev])
      await sendEventToHIDS(username, 'success')
      setScreen('success')
      return
    }

    // ── Wrong credentials ───────────────────────────────────────────────
    const newCount = failCount + 1
    setAttempts(prev => [{
      id: Date.now(),
      username,
      status: 'fail',
      time: now.toLocaleTimeString(),
      message: `Attempt ${newCount}/${MAX_ATTEMPTS} — invalid credentials`,
    }, ...prev])
    await sendEventToHIDS(username, 'fail')
    setFailCount(newCount)

    // ── 5th failure → HIDS alert ────────────────────────────────────────
    if (newCount >= MAX_ATTEMPTS) {
      setAlert({
        alert_id: crypto.randomUUID(),
        severity: 'HIGH',
        attack_type: 'brute_force',
        username,
        source_ip: SOURCE_IP,
        failed_attempts: newCount,
        timestamp: Math.floor(Date.now() / 1000),
        description:
          `${newCount} consecutive failed login attempts for user "${username}" ` +
          `from ${SOURCE_IP}. Brute-force attack detected.`,
      })
      setScreen('alert')
    }
  }, [failCount, sendEventToHIDS])

  // Full reset → back to clean login form
  const handleReset = useCallback(() => {
    setScreen('login')
    setFailCount(0)
    setAlert(null)
    setAttempts([])
    setLastUsername('')
  }, [])

  const handleLockAccount = useCallback(() => setScreen('locked'), [])

  const handleLogout = useCallback(() => {
    setScreen('login')
    setFailCount(0)
    setAttempts([])
    setLastUsername('')
  }, [])

  return (
    <div style={styles.root}>
      {/* ── Main panel ── */}
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
            onLogout={handleLogout}
          />
        )}
      </div>

      {/* ── Right panel: live attempt log ── */}
      <AttemptLog
        attempts={attempts}
        failCount={failCount}
        maxAttempts={MAX_ATTEMPTS}
      />
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
