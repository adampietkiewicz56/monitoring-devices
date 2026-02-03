import React, { useState, useEffect } from 'react'
import { hostsAPI, alertsAPI, authAPI, hostgroupsAPI } from '../services/api'
import HostList from '../components/HostList'
import AlertList from '../components/AlertList'
import AddHostModal from '../components/AddHostModal'
import ConfirmModal from '../components/ConfirmModal'
import HostGroupsPanel from '../components/HostGroupsPanel'
import './Dashboard.css'

function Dashboard({ user, onLogout }) {
  const [hosts, setHosts] = useState([])
  const [alerts, setAlerts] = useState([])
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [notifications, setNotifications] = useState([])
  const [confirmDelete, setConfirmDelete] = useState(null) // { id, name }
  const [confirmGroupDelete, setConfirmGroupDelete] = useState(null) // { id, name }

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
      const [hostsRes, alertsRes, groupsRes] = await Promise.all([
        hostsAPI.getAll(),
        alertsAPI.getAll(),
        hostgroupsAPI.getAll()
      ])
      setHosts(hostsRes.data)
      setAlerts(alertsRes.data)
      setGroups(groupsRes.data)
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

  const handleAssignGroup = async (host, groupIdValue) => {
    const groupId = groupIdValue ? Number(groupIdValue) : null
    try {
      await hostsAPI.update(host.id, {
        name: host.name,
        ip: host.ip,
        group_id: groupId
      })
      loadData()
    } catch (err) {
      alert('Failed to update group: ' + (err.response?.data?.detail || 'Error'))
    }
  }

  const handleDelete = async (id) => {
    const host = hosts.find(h => h.id === id)
    setConfirmDelete({ id, name: host?.name || 'this host' })
  }

  const confirmDeleteAction = async () => {
    try {
      await hostsAPI.delete(confirmDelete.id)
      loadData()
      setConfirmDelete(null)
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || 'Permission denied'))
      setConfirmDelete(null)
    }
  }

  const handleCreateGroup = async (data) => {
    try {
      await hostgroupsAPI.create(data)
      loadData()
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Permission denied')
    }
  }

  const handleDeleteGroup = (group) => {
    setConfirmGroupDelete({ id: group.id, name: group.name })
  }

  const confirmDeleteGroupAction = async () => {
    try {
      await hostgroupsAPI.delete(confirmGroupDelete.id)
      loadData()
      setConfirmGroupDelete(null)
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || 'Permission denied'))
      setConfirmGroupDelete(null)
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
            <HostList
              hosts={hosts}
              onDelete={handleDelete}
              role={user.role}
              groups={groups}
              onAssignGroup={handleAssignGroup}
            />
            <HostGroupsPanel
              groups={groups}
              role={user.role}
              onCreate={handleCreateGroup}
              onDelete={handleDeleteGroup}
            />
            <div className="alerts-section">
              <h2>Recent Alerts</h2>
              <AlertList alerts={alerts.slice(0, 10)} />
      {confirmDelete && (
        <ConfirmModal
          message={`Are you sure you want to delete "${confirmDelete.name}"? This action cannot be undone.`}
          onConfirm={confirmDeleteAction}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
      {confirmGroupDelete && (
        <ConfirmModal
          message={`Are you sure you want to delete group "${confirmGroupDelete.name}"?`}
          onConfirm={confirmDeleteGroupAction}
          onCancel={() => setConfirmGroupDelete(null)}
        />
      )}
            </div>
          </>
        )}
      </div>

      {showModal && <AddHostModal onClose={() => setShowModal(false)} onAdd={handleAdd} groups={groups} />}
    </div>
  )
}

export default Dashboard
