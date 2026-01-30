import React from 'react'
import './AlertList.css'

function AlertList({ alerts }) {
  return (
    <div className="alert-list">
      {alerts.length === 0 ? (
        <div className="empty">No alerts</div>
      ) : (
        alerts.map(alert => (
          <div key={alert.id} className={`alert-item ${alert.severity.toLowerCase()}`}>
            <div className="alert-header">
              <div className="alert-host">
                <strong>{alert.host?.name || 'Unknown'}</strong>
                <span className="ip">{alert.host?.ip || 'N/A'}</span>
              </div>
              <div className="alert-meta">
                <span className="severity">{alert.severity}</span>
                <span className="time">{new Date(alert.timestamp).toLocaleString()}</span>
              </div>
            </div>
            <div className="message">{alert.message}</div>
          </div>
        ))
      )}
    </div>
  )
}

export default AlertList
