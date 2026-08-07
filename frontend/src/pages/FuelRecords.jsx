import { useEffect, useState } from 'react'
import { 
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Edit2,
  Fuel,
  Plus,
  Search,
  Trash2,
  Users,
  Truck,
  X,
} from 'lucide-react'
import { analyticsService, driverService, fuelRecordService, getApiErrorMessage, vehicleService } from '../services/api'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const WRITE_ROLES = ['Admin', 'Fleet Manager', 'Dispatcher']
const READ_ROLES = ['Admin', 'Fleet Manager', 'Dispatcher', 'Driver']

function getCurrentRole() {
  try {
    const storedUser = localStorage.getItem('fleetflow_user')
    if (!storedUser) {
      return 'Fleet Manager'
    }

    const parsedUser = JSON.parse(storedUser)
    return parsedUser?.role || 'Fleet Manager'
  } catch {
    return 'Fleet Manager'
  }
}

function formatDateForInput(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}

export default function FuelRecords() {
  const [records, setRecords] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers] = useState([])
  const [analytics, setAnalytics] = useState({
    total_fuel_consumed: 0,
    total_fuel_cost: 0,
    average_fuel_consumption: 0,
    vehicle_with_highest_fuel_usage: null,
    vehicle_with_lowest_fuel_usage: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 8

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [submitError, setSubmitError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [deleteConfirmId, setDeleteConfirmId] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [toasts, setToasts] = useState([])

  const [formData, setFormData] = useState({
    vehicle_id: '',
    driver_id: '',
    fuel_quantity: '',
    fuel_cost: '',
    odometer_reading: '',
    fuel_date: '',
    fuel_station: '',
    remarks: '',
  })

  const role = getCurrentRole()
  const canWrite = WRITE_ROLES.includes(role)
  const canRead = READ_ROLES.includes(role)

  useEffect(() => {
    loadData()
  }, [])

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
      const [recordsRes, vehiclesRes, driversRes, analyticsRes] = await Promise.all([
        fuelRecordService.getAll(),
        vehicleService.getAll(),
        driverService.getAll(),
        analyticsService.getOperations().catch(() => null),
      ])

      setRecords(recordsRes.data || [])
      setVehicles(vehiclesRes.data || [])
      setDrivers(driversRes.data || [])
      if (analyticsRes?.data) {
        setAnalytics(analyticsRes.data)
      }

      const fuelAnalyticsRes = await fuelRecordService.getAnalytics()
      setAnalytics(fuelAnalyticsRes.data || analytics)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load fuel records or supporting fleet data.'))
    } finally {
      setLoading(false)
    }
  }

  const handleOpenAddModal = () => {
    setEditingRecord(null)
    setFormData({
      vehicle_id: '',
      driver_id: '',
      fuel_quantity: '',
      fuel_cost: '',
      odometer_reading: '',
      fuel_date: '',
      fuel_station: '',
      remarks: '',
    })
    setSubmitError('')
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (record) => {
    setEditingRecord(record)
    setFormData({
      vehicle_id: record.vehicle_id?.toString() || '',
      driver_id: record.driver_id?.toString() || '',
      fuel_quantity: record.fuel_quantity?.toString() || '',
      fuel_cost: record.fuel_cost?.toString() || '',
      odometer_reading: record.odometer_reading?.toString() || '',
      fuel_date: formatDateForInput(record.fuel_date),
      fuel_station: record.fuel_station || '',
      remarks: record.remarks || '',
    })
    setSubmitError('')
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingRecord(null)
  }

  const handleInputChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
    if (submitError) setSubmitError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (
      !formData.vehicle_id ||
      !formData.driver_id ||
      !formData.fuel_quantity ||
      !formData.fuel_cost ||
      !formData.odometer_reading ||
      !formData.fuel_date
    ) {
      setSubmitError('Vehicle, driver, quantity, cost, odometer, and date are required.')
      return
    }

    setSubmitting(true)
    setSubmitError('')

    const payload = {
      vehicle_id: parseInt(formData.vehicle_id, 10),
      driver_id: parseInt(formData.driver_id, 10),
      fuel_quantity: parseFloat(formData.fuel_quantity),
      fuel_cost: parseFloat(formData.fuel_cost),
      odometer_reading: parseFloat(formData.odometer_reading),
      fuel_date: formData.fuel_date,
      fuel_station: formData.fuel_station.trim() || null,
      remarks: formData.remarks.trim() || null,
    }

    try {
      if (editingRecord) {
        await fuelRecordService.update(editingRecord.id, payload)
        addToast('Fuel record updated successfully.')
      } else {
        await fuelRecordService.create(payload)
        addToast('Fuel record added successfully.')
      }

      await loadData()
      handleCloseModal()
    } catch (err) {
      setSubmitError(getApiErrorMessage(err, 'Failed to save the fuel record.'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmId) return

    setDeleting(true)
    try {
      await fuelRecordService.remove(deleteConfirmId)
      addToast('Fuel record deleted successfully.')
      await loadData()
    } catch (err) {
      addToast(getApiErrorMessage(err, 'Failed to delete fuel record.'), 'error')
    } finally {
      setDeleting(false)
      setDeleteConfirmId(null)
    }
  }

  const getVehicleLabel = (vehicleId) => {
    const vehicle = vehicles.find((item) => item.id === vehicleId)
    if (!vehicle) return `Vehicle #${vehicleId}`
    return `${vehicle.vehicle_number} ${vehicle.registration_number ? `(${vehicle.registration_number})` : ''}`.trim()
  }

  const getDriverLabel = (driverId) => {
    const driver = drivers.find((item) => item.id === driverId)
    if (!driver) return `Driver #${driverId}`
    return driver.name
  }

  const filteredRecords = records.filter((record) => {
    const vehicle = vehicles.find((item) => item.id === record.vehicle_id)
    const driver = drivers.find((item) => item.id === record.driver_id)
    const haystack = [
      record.id,
      record.fuel_station,
      record.remarks,
      vehicle?.vehicle_number,
      vehicle?.registration_number,
      driver?.name,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(searchTerm.toLowerCase())
  })

  const totalPages = Math.ceil(filteredRecords.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const paginatedRecords = filteredRecords.slice(startIndex, startIndex + itemsPerPage)

  const highestVehicle = analytics.vehicle_with_highest_fuel_usage
  const lowestVehicle = analytics.vehicle_with_lowest_fuel_usage

  // Fuel trend by month for chart
  const fuelTrendMap = records.reduce((acc, f) => {
    if (!f.fuel_date) return acc
    const month = f.fuel_date.slice(0, 7)
    if (!acc[month]) acc[month] = { month, quantity: 0, cost: 0 }
    acc[month].quantity = parseFloat((acc[month].quantity + Number(f.fuel_quantity || 0)).toFixed(2))
    acc[month].cost = parseFloat((acc[month].cost + Number(f.fuel_cost || 0)).toFixed(2))
    return acc
  }, {})
  const fuelTrendData = Object.values(fuelTrendMap).sort((a, b) => a.month.localeCompare(b.month))

  if (!canRead) {
    return null
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
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

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">Fuel Records</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Track fuel transactions, verify vehicle and driver usage, and review live fuel analytics.
          </p>
        </div>
        {canWrite && (
          <button className="btn btn--primary" onClick={handleOpenAddModal}>
            <Plus style={{ width: '16px', height: '16px' }} />
            <span>Add Fuel Record</span>
          </button>
        )}
      </div>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Fuel style={{ width: '18px', height: '18px', color: 'var(--primary)' }} />
            <span className="card-title">Total Fuel Consumed</span>
          </div>
          <strong style={{ fontSize: '24px' }}>{Number(analytics.total_fuel_consumed || 0).toFixed(2)}</strong>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <BarChart3 style={{ width: '18px', height: '18px', color: 'var(--warning)' }} />
            <span className="card-title">Total Fuel Cost</span>
          </div>
          <strong style={{ fontSize: '24px' }}>{Number(analytics.total_fuel_cost || 0).toFixed(2)}</strong>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Truck style={{ width: '18px', height: '18px', color: 'var(--success)' }} />
            <span className="card-title">Average Fuel Consumption</span>
          </div>
          <strong style={{ fontSize: '24px' }}>{Number(analytics.average_fuel_consumption || 0).toFixed(2)}</strong>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users style={{ width: '18px', height: '18px', color: 'var(--text-secondary)' }} />
            <span className="card-title">Highest Fuel Usage</span>
          </div>
          <strong style={{ fontSize: '14px' }}>
            {highestVehicle
              ? `${highestVehicle.vehicle_number || `Vehicle ${highestVehicle.vehicle_id}`} - ${Number(highestVehicle.total_fuel_consumed || 0).toFixed(2)}`
              : 'No fuel records found'}
          </strong>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users style={{ width: '18px', height: '18px', color: 'var(--text-secondary)' }} />
            <span className="card-title">Lowest Fuel Usage</span>
          </div>
          <strong style={{ fontSize: '14px' }}>
            {lowestVehicle
              ? `${lowestVehicle.vehicle_number || `Vehicle ${lowestVehicle.vehicle_id}`} - ${Number(lowestVehicle.total_fuel_consumed || 0).toFixed(2)}`
              : 'No fuel records found'}
          </strong>
        </div>
      </section>



      {error ? (
        <div className="error-card">
          <AlertCircle className="error-card__icon" />
          <h2 className="error-card__title">Retrieve Failed</h2>
          <p className="error-card__desc">{error}</p>
          <button className="btn btn--primary" onClick={loadData}>
            Retry Load
          </button>
        </div>
      ) : loading ? (
        <div className="loading-container" style={{ minHeight: '40vh' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : (
        <div className="datagrid-container">
          <div className="datagrid-header-bar">
            <label className="navbar__search" style={{ maxWidth: '360px', margin: 0 }} htmlFor="fuel-search">
              <Search className="navbar__searchIcon" aria-hidden="true" />
              <input
                id="fuel-search"
                className="navbar__searchInput"
                type="search"
                placeholder="Search by vehicle, driver, or station..."
                value={searchTerm}
                onChange={(event) => {
                  setSearchTerm(event.target.value)
                  setCurrentPage(1)
                }}
              />
            </label>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
              Showing {filteredRecords.length} {filteredRecords.length === 1 ? 'record' : 'records'}
            </span>
          </div>

          <div className="datagrid-wrapper">
            <table className="datagrid">
              <thead>
                <tr>
                  <th>Record</th>
                  <th>Vehicle</th>
                  <th>Driver</th>
                  <th>Quantity</th>
                  <th>Cost</th>
                  <th>Date</th>
                  <th>Station</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRecords.length > 0 ? (
                  paginatedRecords.map((record) => (
                    <tr key={record.id}>
                      <td style={{ fontWeight: 600 }}>#{record.id}</td>
                      <td>{getVehicleLabel(record.vehicle_id)}</td>
                      <td>{getDriverLabel(record.driver_id)}</td>
                      <td>{Number(record.fuel_quantity || 0).toFixed(2)}</td>
                      <td>{Number(record.fuel_cost || 0).toFixed(2)}</td>
                      <td>{formatDateForInput(record.fuel_date)}</td>
                      <td>{record.fuel_station || 'N/A'}</td>
                      <td>
                        {canWrite ? (
                          <div className="datagrid-actions">
                            <button
                              className="btn btn--secondary"
                              style={{ padding: '6px 10px', fontSize: '12px' }}
                              onClick={() => handleOpenEditModal(record)}
                            >
                              <Edit2 style={{ width: '13px', height: '13px' }} />
                              <span>Edit</span>
                            </button>
                            <button
                              className="btn btn--outline-danger"
                              style={{ padding: '6px 10px', fontSize: '12px' }}
                              onClick={() => setDeleteConfirmId(record.id)}
                            >
                              <Trash2 style={{ width: '13px', height: '13px' }} />
                              <span>Delete</span>
                            </button>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Read only</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8">
                      <div className="empty-state">
                        <Fuel className="empty-state__icon" />
                        <p className="empty-state__title">No fuel records found</p>
                        <p className="empty-state__desc">Create a fuel record to start tracking fuel usage and costs.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <span className="pagination__info">
                Page {currentPage} of {totalPages}
              </span>
              <div className="pagination__buttons">
                <button
                  className="btn btn--secondary"
                  style={{ padding: '6px 12px' }}
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((current) => current - 1)}
                >
                  <ChevronLeft style={{ width: '16px', height: '16px' }} />
                  <span>Previous</span>
                </button>
                <button
                  className="btn btn--secondary"
                  style={{ padding: '6px 12px' }}
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((current) => current + 1)}
                >
                  <span>Next</span>
                  <ChevronRight style={{ width: '16px', height: '16px' }} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {isModalOpen && canWrite && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '560px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{editingRecord ? 'Update Fuel Record' : 'Add Fuel Record'}</h3>
              <button className="modal__close" onClick={handleCloseModal} aria-label="Close modal">
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal__body">
                {submitError && (
                  <div className="login-form__error" style={{ marginBottom: '16px' }}>
                    <AlertCircle className="toast-icon" />
                    <span>{submitError}</span>
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="vehicle_id">Vehicle</label>
                    <select
                      className="form-select"
                      id="vehicle_id"
                      name="vehicle_id"
                      value={formData.vehicle_id}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="">Select vehicle</option>
                      {vehicles.map((vehicle) => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.vehicle_number} {vehicle.registration_number ? `(${vehicle.registration_number})` : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="driver_id">Driver</label>
                    <select
                      className="form-select"
                      id="driver_id"
                      name="driver_id"
                      value={formData.driver_id}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="">Select driver</option>
                      {drivers.map((driver) => (
                        <option key={driver.id} value={driver.id}>
                          {driver.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="fuel_quantity">Fuel Quantity</label>
                    <input
                      className="form-input"
                      type="number"
                      id="fuel_quantity"
                      name="fuel_quantity"
                      value={formData.fuel_quantity}
                      onChange={handleInputChange}
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="fuel_cost">Fuel Cost</label>
                    <input
                      className="form-input"
                      type="number"
                      id="fuel_cost"
                      name="fuel_cost"
                      value={formData.fuel_cost}
                      onChange={handleInputChange}
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="odometer_reading">Odometer Reading</label>
                    <input
                      className="form-input"
                      type="number"
                      id="odometer_reading"
                      name="odometer_reading"
                      value={formData.odometer_reading}
                      onChange={handleInputChange}
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="fuel_date">Fuel Date</label>
                    <input
                      className="form-input"
                      type="date"
                      id="fuel_date"
                      name="fuel_date"
                      value={formData.fuel_date}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="fuel_station">Fuel Station</label>
                  <input
                    className="form-input"
                    type="text"
                    id="fuel_station"
                    name="fuel_station"
                    value={formData.fuel_station}
                    onChange={handleInputChange}
                    placeholder="Optional station name"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="remarks">Remarks</label>
                  <textarea
                    className="form-input"
                    id="remarks"
                    name="remarks"
                    value={formData.remarks}
                    onChange={handleInputChange}
                    placeholder="Optional notes"
                    rows="3"
                  />
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={handleCloseModal} disabled={submitting}>
                  Cancel
                </button>
                <button type="submit" className="btn btn--primary" disabled={submitting}>
                  {submitting ? 'Saving changes...' : editingRecord ? 'Update Fuel Record' : 'Add Fuel Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteConfirmId && canWrite && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '400px' }}>
            <div className="modal__header">
              <h3 className="modal__title" style={{ color: 'var(--danger)' }}>Delete Confirmation</h3>
              <button className="modal__close" onClick={() => setDeleteConfirmId(null)} aria-label="Close delete modal">
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>
            <div className="modal__body">
              <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', lineHeight: '1.5' }}>
                Are you sure you want to delete this fuel record? This action cannot be undone.
              </p>
            </div>
            <div className="modal__footer">
              <button className="btn btn--secondary" onClick={() => setDeleteConfirmId(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="btn btn--danger" onClick={handleDeleteConfirm} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}