import React, { useState } from 'react'
import './AddHostModal.css'

function AddHostModal({ onClose, onAdd }) {
  const [name, setName] = useState('')
  const [ip, setIp] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onAdd({ name, ip })
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Add New Host</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. Server 1"
            />
          </div>
          <div className="form-group">
            <label>IP Address</label>
            <input
              type="text"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              required
              placeholder="e.g. 192.168.1.10"
            />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-success">Add Host</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddHostModal
