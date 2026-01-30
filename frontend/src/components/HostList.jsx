import React from 'react'
import './HostList.css'

function HostList({ hosts, onDelete, role }) {
  const getStatusColor = (status) => {
    if (status === 'UP') return 'green'
    if (status === 'DOWN') return 'red'
    return 'gray'
  }

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
