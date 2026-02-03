import React, { useState } from 'react'
import { authAPI } from '../services/api'
import './Login.css'

function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isRegister, setIsRegister] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isRegister) {
        // Register
        const res = await authAPI.register(username, password, email)
        const { access_token, username: user, role } = res.data
        onLogin(access_token, user, role)
      } else {
        // Login
        const res = await authAPI.login(username, password)
        const { access_token, username: user, role } = res.data
        onLogin(access_token, user, role)
      }
    } catch (err) {
      setError(err.response?.data?.detail || (isRegister ? 'Registration failed' : 'Login failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🖥️ Network Monitoring</h1>
        <h2>{isRegister ? 'Register' : 'Login'}</h2>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          
          {isRegister && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>
          )}
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (isRegister ? 'Registering...' : 'Logging in...') : (isRegister ? 'Register' : 'Login')}
          </button>
        </form>
        
        <div className="toggle-auth">
          <p>
            {isRegister ? 'Already have account?' : "Don't have account?"}
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
                setUsername('')
                setPassword('')
                setEmail('')
              }}
              className="link-btn"
            >
              {isRegister ? ' Login' : ' Register'}
            </button>
          </p>
        </div>
        
        {!isRegister && (
          <div className="info">
            <p><strong>Admin:</strong> admin / admin123</p>
            <p><strong>User:</strong> user1 / user123</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Login
