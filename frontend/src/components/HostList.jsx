import React from 'react'
import './HostList.css'

function HostList({ hosts, onDelete, role, groups = [], onAssignGroup }) {
  const getStatusColor = (status) => {
    if (status === 'UP') return 'green'
    if (status === 'DOWN') return 'red'
    return 'gray'
  }

  const canEditGroup = role === 'ADMIN' || role === 'USER'

  return (
    <div className="host-list">
      {hosts.length === 0 ? (
        <div className="empty">No hosts found</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Name</th>
              <th>IP Address</th>
              <th>Group</th>
              <th>Last Seen</th>
              {role === 'ADMIN' && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {hosts.map(host => (
              <tr key={host.id}>
                <td>
                  <span className={`status ${getStatusColor(host.status)}`}>
                    {host.status}
                  </span>
                </td>
                <td>{host.name}</td>
                <td>{host.ip}</td>
                <td>
                  {canEditGroup ? (
                    <select
                      className="group-select"
                      value={host.group_id || ''}
                      onChange={(e) => onAssignGroup(host, e.target.value)}
                    >
                      <option value="">None</option>
                      {groups.map((g) => (
                        <option key={g.id} value={g.id}>{g.name}</option>
                      ))}
                    </select>
                  ) : (
                    <span>
                      {groups.find((g) => g.id === host.group_id)?.name || 'None'}
                    </span>
                  )}
                </td>
                <td>{new Date(host.last_seen).toLocaleString()}</td>
                {role === 'ADMIN' && (
                  <td>
                    <button onClick={() => onDelete(host.id)} className="btn-danger btn-sm">
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

export default HostList
