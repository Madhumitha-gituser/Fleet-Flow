import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  Gauge,
  Pencil,
  RefreshCcw,
  Save,
  Trash2,
  Users,
} from 'lucide-react'
import {
  driverService,
  vehicleService,
  tripService,
  driverAssignmentService,
  driverAttendanceService,
  driverPerformanceService,
  getApiErrorMessage,
} from '../services/api'

const assignmentStatuses = ['Active', 'Inactive', 'Completed']
const attendanceStatuses = ['Present', 'Absent', 'Leave']

function toInputDate(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}

function toInputDateTime(value) {
  if (!value) return ''
  return String(value).slice(0, 16)
}

function displayDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}

function displayDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export default function DriverOperations() {
  const [drivers, setDrivers] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [trips, setTrips] = useState([])
  const [assignments, setAssignments] = useState([])
  const [attendance, setAttendance] = useState([])
  const [performance, setPerformance] = useState(null)
  const [selectedDriverId, setSelectedDriverId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submittingAssignment, setSubmittingAssignment] = useState(false)
  const [submittingAttendance, setSubmittingAttendance] = useState(false)
  const [assignmentEditingId, setAssignmentEditingId] = useState(null)
  const [attendanceEditingId, setAttendanceEditingId] = useState(null)
  const [toasts, setToasts] = useState([])

  const [assignmentForm, setAssignmentForm] = useState({
    driver_id: '',
    vehicle_id: '',
    trip_id: '',
    assignment_date: '',
    assignment_status: 'Active',
    remarks: '',
  })

  const [attendanceForm, setAttendanceForm] = useState({
    driver_id: '',
    date: '',
    attendance_status: 'Present',
    check_in_time: '',
    check_out_time: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const driverLookup = useMemo(() => {
    return drivers.reduce((accumulator, driver) => {
      accumulator[driver.id] = driver
      return accumulator
    }, {})
  }, [drivers])

  const vehicleLookup = useMemo(() => {
    return vehicles.reduce((accumulator, vehicle) => {
      accumulator[vehicle.id] = vehicle
      return accumulator
    }, {})
  }, [vehicles])

  const tripLookup = useMemo(() => {
    return trips.reduce((accumulator, trip) => {
      accumulator[trip.id] = trip
      return accumulator
    }, {})
  }, [trips])

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
      const [driversRes, vehiclesRes, tripsRes, assignmentsRes, attendanceRes] = await Promise.all([
        driverService.getAll(),
        vehicleService.getAll(),
        tripService.getAll(),
        driverAssignmentService.getAll(),
        driverAttendanceService.getAll(),
      ])
      setDrivers(driversRes.data || [])
      setVehicles(vehiclesRes.data || [])
      setTrips(tripsRes.data || [])
      setAssignments(assignmentsRes.data || [])
      setAttendance(attendanceRes.data || [])
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load driver operations.'))
    } finally {
      setLoading(false)
    }
  }

  const resetAssignmentForm = () => {
    setAssignmentEditingId(null)
    setAssignmentForm({
      driver_id: '',
      vehicle_id: '',
      trip_id: '',
      assignment_date: '',
      assignment_status: 'Active',
      remarks: '',
    })
  }

  const resetAttendanceForm = () => {
    setAttendanceEditingId(null)
    setAttendanceForm({
      driver_id: '',
      date: '',
      attendance_status: 'Present',
      check_in_time: '',
      check_out_time: '',
    })
  }

  const handleAssignmentChange = (event) => {
    const { name, value } = event.target
    setAssignmentForm((current) => ({ ...current, [name]: value }))
  }

  const handleAttendanceChange = (event) => {
    const { name, value } = event.target
    setAttendanceForm((current) => ({ ...current, [name]: value }))
  }

  const handleAssignmentEdit = (assignment) => {
    setAssignmentEditingId(assignment.id)
    setAssignmentForm({
      driver_id: String(assignment.driver_id || ''),
      vehicle_id: String(assignment.vehicle_id || ''),
      trip_id: assignment.trip_id ? String(assignment.trip_id) : '',
      assignment_date: toInputDate(assignment.assignment_date),
      assignment_status: assignment.assignment_status || 'Active',
      remarks: assignment.remarks || '',
    })
  }

  const handleAttendanceEdit = (record) => {
    setAttendanceEditingId(record.id)
    setAttendanceForm({
      driver_id: String(record.driver_id || ''),
      date: toInputDate(record.date),
      attendance_status: record.attendance_status || 'Present',
      check_in_time: toInputDateTime(record.check_in_time),
      check_out_time: toInputDateTime(record.check_out_time),
    })
  }

  const handleAssignmentSubmit = async (event) => {
    event.preventDefault()
    if (!assignmentForm.driver_id || !assignmentForm.vehicle_id || !assignmentForm.assignment_date) {
      setError('Assignment requires a driver, vehicle, and date.')
      return
    }

    try {
      setSubmittingAssignment(true)
      setError('')
      const payload = {
        driver_id: Number(assignmentForm.driver_id),
        vehicle_id: Number(assignmentForm.vehicle_id),
        trip_id: assignmentForm.trip_id ? Number(assignmentForm.trip_id) : null,
        assignment_date: assignmentForm.assignment_date,
        assignment_status: assignmentForm.assignment_status,
        remarks: assignmentForm.remarks || null,
      }

      if (assignmentEditingId) {
        const response = await driverAssignmentService.update(assignmentEditingId, payload)
        setAssignments((current) => current.map((item) => (item.id === assignmentEditingId ? response.data : item)))
        addToast('Driver assignment updated successfully.')
      } else {
        const response = await driverAssignmentService.create(payload)
        setAssignments((current) => [response.data, ...current])
        addToast('Driver assignment created successfully.')
      }

      resetAssignmentForm()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save driver assignment.'))
    } finally {
      setSubmittingAssignment(false)
    }
  }

  const handleAttendanceSubmit = async (event) => {
    event.preventDefault()
    if (!attendanceForm.driver_id || !attendanceForm.date) {
      setError('Attendance requires a driver and a date.')
      return
    }

    try {
      setSubmittingAttendance(true)
      setError('')
      const payload = {
        driver_id: Number(attendanceForm.driver_id),
        date: attendanceForm.date,
        attendance_status: attendanceForm.attendance_status,
        check_in_time: attendanceForm.check_in_time || null,
        check_out_time: attendanceForm.check_out_time || null,
      }

      if (attendanceEditingId) {
        const response = await driverAttendanceService.update(attendanceEditingId, payload)
        setAttendance((current) => current.map((item) => (item.id === attendanceEditingId ? response.data : item)))
        addToast('Driver attendance updated successfully.')
      } else {
        const response = await driverAttendanceService.create(payload)
        setAttendance((current) => [response.data, ...current])
        addToast('Driver attendance created successfully.')
      }

      resetAttendanceForm()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save attendance record.'))
    } finally {
      setSubmittingAttendance(false)
    }
  }

  const handleAssignmentDelete = async (assignmentId) => {
    try {
      await driverAssignmentService.remove(assignmentId)
      setAssignments((current) => current.filter((item) => item.id !== assignmentId))
      addToast('Driver assignment removed successfully.')
    } catch (err) {
      addToast(getApiErrorMessage(err, 'Failed to remove assignment.'), 'error')
    }
  }

  const handleAttendanceDelete = async (attendanceId) => {
    try {
      await driverAttendanceService.remove(attendanceId)
      setAttendance((current) => current.filter((item) => item.id !== attendanceId))
      addToast('Driver attendance removed successfully.')
    } catch (err) {
      addToast(getApiErrorMessage(err, 'Failed to remove attendance record.'), 'error')
    }
  }

  const handlePerformanceLookup = async () => {
    if (!selectedDriverId) {
      setError('Select a driver to view performance metrics.')
      return
    }

    try {
      setError('')
      const response = await driverPerformanceService.getByDriverId(selectedDriverId)
      setPerformance(response.data)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load driver performance.'))
      setPerformance(null)
    }
  }

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
        <h1 className="page-title">Driver Operations</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Manage assignments, attendance, and performance in one place.
        </p>
      </div>

      {error && (
        <div className="error-card" style={{ padding: '16px' }}>
          <AlertCircle className="error-card__icon" />
          <div>
            <h3 className="error-card__title" style={{ fontSize: '15px' }}>Action failed</h3>
            <p className="error-card__desc">{error}</p>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: '20px' }}>
        <div className="card__header" style={{ marginBottom: '16px' }}>
          <h2 className="card__title">Driver Assignment</h2>
          <button type="button" className="btn btn--secondary" onClick={resetAssignmentForm}>
            <RefreshCcw style={{ width: '14px', height: '14px' }} />
            <span>Reset</span>
          </button>
        </div>
        <form onSubmit={handleAssignmentSubmit} style={{ display: 'grid', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Driver</span>
              <select className="form-select" name="driver_id" value={assignmentForm.driver_id} onChange={handleAssignmentChange}>
                <option value="">Select driver</option>
                {drivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>{driver.name}</option>
                ))}
              </select>
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Vehicle</span>
              <select className="form-select" name="vehicle_id" value={assignmentForm.vehicle_id} onChange={handleAssignmentChange}>
                <option value="">Select vehicle</option>
                {vehicles.map((vehicle) => (
                  <option key={vehicle.id} value={vehicle.id}>{vehicle.vehicle_number}</option>
                ))}
              </select>
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Trip</span>
              <select className="form-select" name="trip_id" value={assignmentForm.trip_id} onChange={handleAssignmentChange}>
                <option value="">Optional trip</option>
                {trips.map((trip) => (
                  <option key={trip.id} value={trip.id}>{trip.id} - {trip.trip_status}</option>
                ))}
              </select>
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Assignment Date</span>
              <input className="form-input" type="date" name="assignment_date" value={assignmentForm.assignment_date} onChange={handleAssignmentChange} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Status</span>
              <select className="form-select" name="assignment_status" value={assignmentForm.assignment_status} onChange={handleAssignmentChange}>
                {assignmentStatuses.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </label>
          </div>
          <label>
            <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Remarks</span>
            <textarea
              className="form-textarea"
              name="remarks"
              rows="3"
              value={assignmentForm.remarks}
              onChange={handleAssignmentChange}
              placeholder="Optional assignment notes"
            />
          </label>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn--primary" disabled={submittingAssignment}>
              <Save style={{ width: '14px', height: '14px' }} />
              <span>{submittingAssignment ? 'Saving...' : assignmentEditingId ? 'Update Assignment' : 'Assign Driver'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="datagrid-container">
        <div className="datagrid-header-bar">
          <span style={{ fontWeight: 600 }}>Assigned drivers</span>
          <span className="badge badge--warning">{assignments.length} Assignments</span>
        </div>
        <div className="datagrid-wrapper">
          <table className="datagrid">
            <thead>
              <tr>
                <th>ID</th>
                <th>Driver</th>
                <th>Vehicle</th>
                <th>Trip</th>
                <th>Status</th>
                <th>Date</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assignments.length > 0 ? assignments.map((assignment) => (
                <tr key={assignment.id}>
                  <td style={{ fontWeight: 600 }}>{assignment.id}</td>
                  <td>{driverLookup[assignment.driver_id]?.name || `Driver ${assignment.driver_id}`}</td>
                  <td>{vehicleLookup[assignment.vehicle_id]?.vehicle_number || `Vehicle ${assignment.vehicle_id}`}</td>
                  <td>{assignment.trip_id ? tripLookup[assignment.trip_id]?.trip_status || assignment.trip_id : '-'}</td>
                  <td><span className={`badge badge--${String(assignment.assignment_status || '').toLowerCase().replace(/\s+/g, '')}`}>{assignment.assignment_status}</span></td>
                  <td>{displayDate(assignment.assignment_date)}</td>
                  <td>
                    <div className="datagrid-actions">
                      <button type="button" className="btn btn--secondary" onClick={() => handleAssignmentEdit(assignment)}>
                        <Pencil style={{ width: '14px', height: '14px' }} />
                        <span>Edit</span>
                      </button>
                      <button type="button" className="btn btn--secondary" onClick={() => handleAssignmentDelete(assignment.id)}>
                        <Trash2 style={{ width: '14px', height: '14px' }} />
                        <span>Remove</span>
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="7">
                    <div className="empty-state">
                      <Users className="empty-state__icon" />
                      <p className="empty-state__title">No assignments yet</p>
                      <p className="empty-state__desc">Create an assignment to link a driver with a vehicle or trip.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ padding: '20px' }}>
        <div className="card__header" style={{ marginBottom: '16px' }}>
          <h2 className="card__title">Driver Attendance</h2>
          <button type="button" className="btn btn--secondary" onClick={resetAttendanceForm}>
            <RefreshCcw style={{ width: '14px', height: '14px' }} />
            <span>Reset</span>
          </button>
        </div>
        <form onSubmit={handleAttendanceSubmit} style={{ display: 'grid', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Driver</span>
              <select className="form-select" name="driver_id" value={attendanceForm.driver_id} onChange={handleAttendanceChange}>
                <option value="">Select driver</option>
                {drivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>{driver.name}</option>
                ))}
              </select>
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Date</span>
              <input className="form-input" type="date" name="date" value={attendanceForm.date} onChange={handleAttendanceChange} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Status</span>
              <select className="form-select" name="attendance_status" value={attendanceForm.attendance_status} onChange={handleAttendanceChange}>
                {attendanceStatuses.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Check-In Time</span>
              <input className="form-input" type="datetime-local" name="check_in_time" value={attendanceForm.check_in_time} onChange={handleAttendanceChange} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Check-Out Time</span>
              <input className="form-input" type="datetime-local" name="check_out_time" value={attendanceForm.check_out_time} onChange={handleAttendanceChange} />
            </label>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn--primary" disabled={submittingAttendance}>
              <Save style={{ width: '14px', height: '14px' }} />
              <span>{submittingAttendance ? 'Saving...' : attendanceEditingId ? 'Update Attendance' : 'Create Attendance'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="datagrid-container">
        <div className="datagrid-header-bar">
          <span style={{ fontWeight: 600 }}>Attendance records</span>
          <span className="badge badge--warning">{attendance.length} Records</span>
        </div>
        <div className="datagrid-wrapper">
          <table className="datagrid">
            <thead>
              <tr>
                <th>ID</th>
                <th>Driver</th>
                <th>Date</th>
                <th>Status</th>
                <th>Check-In</th>
                <th>Check-Out</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {attendance.length > 0 ? attendance.map((record) => (
                <tr key={record.id}>
                  <td style={{ fontWeight: 600 }}>{record.id}</td>
                  <td>{driverLookup[record.driver_id]?.name || `Driver ${record.driver_id}`}</td>
                  <td>{displayDate(record.date)}</td>
                  <td><span className={`badge badge--${String(record.attendance_status || '').toLowerCase().replace(/\s+/g, '')}`}>{record.attendance_status}</span></td>
                  <td>{displayDateTime(record.check_in_time)}</td>
                  <td>{displayDateTime(record.check_out_time)}</td>
                  <td>
                    <div className="datagrid-actions">
                      <button type="button" className="btn btn--secondary" onClick={() => handleAttendanceEdit(record)}>
                        <Pencil style={{ width: '14px', height: '14px' }} />
                        <span>Edit</span>
                      </button>
                      <button type="button" className="btn btn--secondary" onClick={() => handleAttendanceDelete(record.id)}>
                        <Trash2 style={{ width: '14px', height: '14px' }} />
                        <span>Remove</span>
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="7">
                    <div className="empty-state">
                      <ClipboardList className="empty-state__icon" />
                      <p className="empty-state__title">No attendance records yet</p>
                      <p className="empty-state__desc">Record attendance to keep track of duty status and time logs.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ padding: '20px' }}>
        <div className="card__header" style={{ marginBottom: '16px' }}>
          <h2 className="card__title">Driver Performance</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) auto', gap: '12px', alignItems: 'end' }}>
          <label>
            <span style={{ display: 'block', marginBottom: '6px', fontWeight: 600 }}>Driver</span>
            <select className="form-select" value={selectedDriverId} onChange={(event) => setSelectedDriverId(event.target.value)}>
              <option value="">Select driver</option>
              {drivers.map((driver) => (
                <option key={driver.id} value={driver.id}>{driver.name}</option>
              ))}
            </select>
          </label>
          <button type="button" className="btn btn--primary" onClick={handlePerformanceLookup}>
            <Gauge style={{ width: '14px', height: '14px' }} />
            <span>View Performance</span>
          </button>
        </div>

        {performance ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginTop: '20px' }}>
            {[
              ['Driver', performance.driver_name],
              ['Total Trips', performance.total_trips],
              ['Completed Trips', performance.completed_trips],
              ['Active Trips', performance.active_trips],
              ['Cancelled Trips', performance.cancelled_trips],
            ].map(([label, value]) => (
              <div key={label} className="card" style={{ padding: '16px', backgroundColor: '#FAFCFD' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>{label}</div>
                <div style={{ fontSize: '20px', fontWeight: 700 }}>{value}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state" style={{ marginTop: '20px' }}>
            <Gauge className="empty-state__icon" />
            <p className="empty-state__title">Select a driver to calculate performance</p>
            <p className="empty-state__desc">The API computes trip totals directly from the Trip table.</p>
          </div>
        )}
      </div>

      {loading && (
        <div className="loading-container" style={{ minHeight: '20vh' }}>
          <div className="loading-spinner"></div>
        </div>
      )}
    </div>
  )
}