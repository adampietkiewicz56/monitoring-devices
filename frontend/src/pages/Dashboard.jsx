import React, { useState, useEffect } from 'react'
import { hostsAPI, alertsAPI, authAPI } from '../services/api'
import HostList from '../components/HostList'
import AlertList from '../components/AlertList'
import AddHostModal from '../components/AddHostModal'
import './Dashboard.css'

function Dashboard({ user, onLogout }) {
  const [hosts, setHosts] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    loadData()
    const ws = new WebSocket('ws://localhost:8000/ws/alerts')
    
    ws.onmessage = (event) => {
      const msg = event.data
      console.log('WebSocket alert:', msg)
      setNotifications(prev => [...prev, { id: Date.now(), msg }])
      
      // Force refresh data after WebSocket message
      setTimeout(() => {
        loadData()
      }, 500)
      
      // Auto-remove notification after 5 seconds
      setTimeout(() => setNotifications(prev => prev.slice(1)), 5000)
    }
    
    return () => ws.close()
  }, [])

  const loadData = async () => {
    try {
      const [hostsRes, alertsRes] = await Promise.all([
        hostsAPI.getAll(),
        alertsAPI.getAll()
      ])
      setHosts(hostsRes.data)
      setAlerts(alertsRes.data)
    } catch (err) {
      console.error('Load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!search) {
      loadData()
      return
    }
    try {
      const res = await hostsAPI.search({ name: search })
      setHosts(res.data)
    } catch (err) {
      console.error('Search error:', err)
    }
  }

  const handleAdd = async (data) => {
    try {
      await hostsAPI.create(data)
      setShowModal(false)
      // Small delay to ensure backend has processed
      setTimeout(() => loadData(), 300)
    } catch (err) {
      alert('Failed to add host: ' + (err.response?.data?.detail || 'Error'))
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this host?')) return
    try {
      await hostsAPI.delete(id)
      loadData()
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || 'Permission denied'))
    }
  }

  const handleLogout = async () => {
    try {
      await authAPI.logout()
    } catch (err) {
      console.error(err)
    }
    onLogout()
  }

  return (
    <div className="dashboard">
      <nav className="navbar">
        <h1>🖥️ Network Monitoring</h1>
        <div className="navbar-user">
          <span>{user.username}</span>
          <span className={`role ${user.role?.toLowerCase()}`}>{user.role}</span>
          <button onClick={handleLogout} className="btn-logout">Logout</button>
        </div>
      </nav>

      {notifications.map(n => (
        <div key={n.id} className="notification">🔔 {n.msg}</div>
      ))}

      <div className="container">
        <div className="header">
          <h2>Hosts</h2>
          <div className="actions">
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button onClick={handleSearch} className="btn-primary">Search</button>
            {(user.role === 'ADMIN' || user.role === 'USER') && (
              <button onClick={() => setShowModal(true)} className="btn-success">+ Add</button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            <HostList hosts={hosts} onDelete={handleDelete} role={user.role} />
            <div className="alerts-section">
              <h2>Recent Alerts</h2>
              <AlertList alerts={alerts.slice(0, 10)} />
            </div>
          </>
        )}
      </div>

      {showModal && <AddHostModal onClose={() => setShowModal(false)} onAdd={handleAdd} />}
    </div>
  )
}

export default Dashboard
