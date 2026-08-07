import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, Info, Pencil, RotateCcw, Save, Wrench, Bell, TrendingUp } from 'lucide-react'
import { maintenanceService, vehicleService, getApiErrorMessage } from '../services/api'


const maintenanceCategories = ['Oil Change', 'Tyre Replacement', 'Brake Service', 'Engine Service', 'General Inspection']
const maintenanceStatuses = ['Scheduled', 'In Progress', 'Completed', 'Cancelled']

function toInputDate(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}

export default function Maintenance() {
  const [records, setRecords] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [toasts, setToasts] = useState([])
  const [formData, setFormData] = useState({
    vehicle_id: '',
    category: maintenanceCategories[0],
    service_date: '',
    next_service_date: '',
    service_cost: '',
    service_provider: '',
    status: 'Scheduled',
    notes: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const vehicleLookup = useMemo(() => {
    return vehicles.reduce((accumulator, vehicle) => {
      accumulator[vehicle.id] = vehicle
      return accumulator
    }, {})
  }, [vehicles])

  const addToast = (message, type = 'success') => {
    const id = Date.now()
    setToasts((current) => [...current, { id, message, type }])
    setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, 4000)
  }

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')
      const [recordsRes, vehiclesRes] = await Promise.all([
        maintenanceService.getAll(),
        vehicleService.getAll(),
      ])
      setRecords(recordsRes.data || [])
      setVehicles(vehiclesRes.data || [])
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load maintenance records.'))
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setEditingId(null)
    setFormData({
      vehicle_id: '',
      category: maintenanceCategories[0],
      service_date: '',
      next_service_date: '',
      service_cost: '',
      service_provider: '',
      status: 'Scheduled',
      notes: '',
    })
  }

  const handleInputChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleEdit = (record) => {
    setEditingId(record.id)
    setFormData({
      vehicle_id: String(record.vehicle_id || ''),
      category: record.category || maintenanceCategories[0],
      service_date: toInputDate(record.service_date),
      next_service_date: toInputDate(record.next_service_date),
      service_cost: record.service_cost ?? '',
      service_provider: record.service_provider || '',
      status: record.status || 'Scheduled',
      notes: record.notes || '',
    })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!formData.vehicle_id || !formData.service_date) {
      setError('Vehicle and service date are required.')
      return
    }

    try {
      setSubmitting(true)
      setError('')
      const payload = {
        vehicle_id: Number(formData.vehicle_id),
        category: formData.category,
        service_date: formData.service_date,
        next_service_date: formData.next_service_date || null,
        service_cost: formData.service_cost === '' ? null : Number(formData.service_cost),
        service_provider: formData.service_provider || null,
        status: formData.status,
        notes: formData.notes || null,
      }

      if (editingId) {
        const response = await maintenanceService.update(editingId, payload)
        setRecords((current) => current.map((record) => (record.id === editingId ? response.data : record)))
        addToast('Maintenance record updated successfully.')
      } else {
        const response = await maintenanceService.create(payload)
        setRecords((current) => [response.data, ...current])
        addToast('Maintenance record created successfully.')
      }

      resetForm()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save maintenance record.'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = async (record) => {
    try {
      const response = await maintenanceService.cancel(record.id)
      setRecords((current) => current.map((item) => (item.id === record.id ? response.data : item)))
      addToast('Maintenance history preserved and record cancelled.')
    } catch (err) {
      addToast(getApiErrorMessage(err, 'Failed to cancel maintenance record.'), 'error')
    }
  }

  // Upcoming alerts: Scheduled or next_service_date within 30 days
  const today = new Date()
  const in30 = new Date(today); in30.setDate(in30.getDate() + 30)
  const alertRecords = records.filter((r) => {
    if (r.status === 'Scheduled') return true
    if (r.next_service_date) {
      const d = new Date(r.next_service_date)
      return d >= today && d <= in30
    }
    return false
  })



  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="toast-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast--${toast.type}`}>
            {toast.type === 'success' ? (
              <CheckCircle2 className="toast-icon toast-icon--success" aria-hidden="true" />
            ) : (
              <AlertCircle className="toast-icon toast-icon--error" aria-hidden="true" />
            )}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>

      <div>
        <h1 className="page-title">Maintenance Records</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Create, update, and cancel maintenance history without deleting records.
        </p>
      </div>

      {/* Maintenance Alerts Panel */}
      <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '14px' }}>
          <Bell style={{ width: '16px', height: '16px', color: '#D97706' }} />
          <h3 style={{ fontWeight: 700, fontSize: '14px' }}>Maintenance Alerts</h3>
          {alertRecords.length > 0 && (
            <span className="badge badge--warning" style={{ marginLeft: 'auto' }}>{alertRecords.length} Pending</span>
          )}
        </div>
        {alertRecords.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '13px', padding: '12px 0' }}>
            <CheckCircle2 style={{ width: '16px', height: '16px', color: '#16A34A' }} />
            <span>No upcoming or scheduled maintenance alerts.</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '220px', overflowY: 'auto' }}>
            {alertRecords.map((r) => {
              const vehicle = vehicleLookup[r.vehicle_id]
              const isOverdue = r.next_service_date && new Date(r.next_service_date) < today
              return (
                <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', background: isOverdue ? '#FEF2F2' : '#FFF7ED', border: `1px solid ${isOverdue ? '#FECACA' : '#FED7AA'}` }}>
                  <div>
                    <p style={{ fontWeight: 600, fontSize: '13px', color: isOverdue ? '#DC2626' : '#92400E' }}>
                      {vehicle?.vehicle_number || `Vehicle ${r.vehicle_id}`} — {r.category}
                    </p>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {r.next_service_date ? `Next service: ${formatDate(r.next_service_date)}` : 'Scheduled — no next date set'}
                    </p>
                  </div>
                  <span className={`badge badge--${isOverdue ? 'danger' : 'warning'}`} style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>
                    {isOverdue ? 'Overdue' : r.status}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>


      <div className="card" style={{ padding: '20px' }}>
        <div className="card__header" style={{ marginBottom: '16px' }}>
          <h2 className="card__title">{editingId ? 'Update maintenance record' : 'Create maintenance record'}</h2>
          <button type="button" className="btn btn--secondary" onClick={resetForm}>
            <RotateCcw style={{ width: '14px', height: '14px' }} />
            <span>Reset</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Vehicle</span>
              <select className="form-select" name="vehicle_id" value={formData.vehicle_id} onChange={handleInputChange}>
                <option value="">Select a vehicle</option>
                {vehicles.map((vehicle) => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.vehicle_number} - {vehicle.vehicle_type}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Category</span>
              <select className="form-select" name="category" value={formData.category} onChange={handleInputChange}>
                {maintenanceCategories.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Service Date</span>
              <input className="form-input" type="date" name="service_date" value={formData.service_date} onChange={handleInputChange} />
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Next Service Date</span>
              <input className="form-input" type="date" name="next_service_date" value={formData.next_service_date} onChange={handleInputChange} />
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Service Cost</span>
              <input className="form-input" type="number" step="0.01" min="0" name="service_cost" value={formData.service_cost} onChange={handleInputChange} />
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Service Provider</span>
              <input className="form-input" type="text" name="service_provider" value={formData.service_provider} onChange={handleInputChange} placeholder="Workshop or vendor name" />
            </label>

            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Status</span>
              <select className="form-select" name="status" value={formData.status} onChange={handleInputChange}>
                {maintenanceStatuses.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </label>
          </div>

          <label>
            <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Notes</span>
            <textarea
              className="form-textarea"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows="3"
              placeholder="Optional work order notes, issue details, or follow-up items"
            />
          </label>

          {error && (
            <div className="error-card" style={{ padding: '16px' }}>
              <AlertCircle className="error-card__icon" />
              <div>
                <h3 className="error-card__title" style={{ fontSize: '15px' }}>Action failed</h3>
                <p className="error-card__desc">{error}</p>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>
              <Info style={{ width: '16px', height: '16px' }} />
              <span>Vehicle IDs are validated by the backend. Maintenance history is never deleted.</span>
            </div>
            <button type="submit" className="btn btn--primary" disabled={submitting}>
              <Save style={{ width: '14px', height: '14px' }} />
              <span>{submitting ? 'Saving...' : editingId ? 'Update Record' : 'Create Record'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="datagrid-container">
        <div className="datagrid-header-bar">
          <span style={{ fontWeight: 600 }}>Maintenance history</span>
          <span className="badge badge--warning">{records.length} Records</span>
        </div>
        <div className="datagrid-wrapper">
          <table className="datagrid">
            <thead>
              <tr>
                <th>ID</th>
                <th>Vehicle</th>
                <th>Category</th>
                <th>Service Date</th>
                <th>Status</th>
                <th>Cost</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.length > 0 ? (
                records.map((record) => {
                  const vehicle = vehicleLookup[record.vehicle_id]
                  return (
                    <tr key={record.id}>
                      <td style={{ fontWeight: 600 }}>{record.id}</td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{vehicle?.vehicle_number || `Vehicle ${record.vehicle_id}`}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{vehicle?.vehicle_type || 'Unknown vehicle'}</div>
                      </td>
                      <td>{record.category}</td>
                      <td>{formatDate(record.service_date)}</td>
                      <td><span className={`badge badge--${String(record.status || '').toLowerCase().replace(/\s+/g, '')}`}>{record.status}</span></td>
                      <td>{record.service_cost ?? '-'}</td>
                      <td>
                        <div className="datagrid-actions">
                          <button type="button" className="btn btn--secondary" onClick={() => handleEdit(record)}>
                            <Pencil style={{ width: '14px', height: '14px' }} />
                            <span>Edit</span>
                          </button>
                          <button type="button" className="btn btn--secondary" onClick={() => handleCancel(record)}>
                            <Wrench style={{ width: '14px', height: '14px' }} />
                            <span>Cancel</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="7">
                    <div className="empty-state">
                      <CheckCircle2 className="empty-state__icon" />
                      <p className="empty-state__title">No maintenance records yet</p>
                      <p className="empty-state__desc">Create the first service entry to begin tracking maintenance history.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {loading && (
        <div className="loading-container" style={{ minHeight: '20vh' }}>
          <div className="loading-spinner"></div>
        </div>
      )}
    </div>
  )
}
