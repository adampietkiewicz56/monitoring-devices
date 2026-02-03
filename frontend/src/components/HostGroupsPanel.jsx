import React, { useState } from 'react'
import './HostGroupsPanel.css'

function HostGroupsPanel({ groups, role, onCreate, onDelete }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    try {
      await onCreate({ name: name.trim(), description: description.trim() || null })
      setName('')
      setDescription('')
    } catch (err) {
      setError(err?.message || 'Failed to create group')
    }
  }

  return (
    <div className="hostgroups">
      <div className="hostgroups-header">
        <h2>Host Groups</h2>
        {role === 'ADMIN' && (
          <form className="hostgroups-form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Group name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <button className="btn-success" type="submit">+ Add group</button>
          </form>
        )}
      </div>

      {error && <div className="hostgroups-error">{error}</div>}

      {groups.length === 0 ? (
        <div className="hostgroups-empty">No groups yet</div>
      ) : (
        <table className="hostgroups-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Hosts</th>
              {role === 'ADMIN' && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.id}>
                <td>{g.name}</td>
                <td>{g.description || '-'}</td>
                <td>{g.host_count ?? 0}</td>
                {role === 'ADMIN' && (
                  <td>
                    <button
                      className="btn-danger btn-sm"
                      onClick={() => onDelete(g)}
                    >
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default HostGroupsPanel
