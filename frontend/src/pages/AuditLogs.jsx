import { useEffect, useState } from 'react'
import { auditLogService, getApiErrorMessage } from '../services/api'
import { 
  Search, 
  RotateCcw,
  ChevronLeft, 
  ChevronRight,
  ClipboardList,
  AlertCircle
} from 'lucide-react'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAction, setSelectedAction] = useState('')
  const [selectedResource, setSelectedResource] = useState('')

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')
      const res = await auditLogService.getAll()
      setLogs(res.data || [])
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to fetch audit log trail.'))
    } finally {
      setLoading(false)
    }
  }

  const handleResetFilters = () => {
    setSearchTerm('')
    setSelectedAction('')
    setSelectedResource('')
    setCurrentPage(1)
  }

  // Filter logs locally for instantaneous user response
  const filteredLogs = logs.filter((log) => {
    const search = searchTerm.toLowerCase()
    const matchesSearch = 
      (log.user_email || '').toLowerCase().includes(search) ||
      (log.details || '').toLowerCase().includes(search) ||
      (log.resource_id || '').toLowerCase().includes(search)

    const matchesAction = selectedAction ? log.action === selectedAction : true
    const matchesResource = selectedResource ? log.resource.toLowerCase() === selectedResource.toLowerCase() : true

    return matchesSearch && matchesAction && matchesResource
  })

  // Pagination math
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage) || 1
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredLogs.slice(indexOfFirstItem, indexOfLastItem)

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

  // Format timestamp helper
  const formatTimestamp = (isoString) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  // Get action status badge class
  const getActionBadgeClass = (action) => {
    switch (action) {
      case 'CREATE':
        return 'badge--success'
      case 'UPDATE':
        return 'badge--warning'
      case 'DELETE':
        return 'badge--danger'
      case 'LOGIN':
        return 'badge--info'
      case 'REGISTER':
        return 'badge--secondary'
      default:
        return 'badge--secondary'
    }
  }

  if (loading && logs.length === 0) {
    return (
      <div className="loading-container" style={{ minHeight: '60vh', flexDirection: 'column', gap: '16px' }}>
        <div className="loading-spinner"></div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Loading system audit trail...</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">System Audit Logs</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Trace security events, resource mutations, and user login history in real-time.
          </p>
        </div>
        <button className="btn btn--primary" onClick={loadData} style={{ padding: '8px 16px' }}>
          Refresh Logs
        </button>
      </div>

      {error && (
        <div className="error-card">
          <AlertCircle className="error-card__icon" />
          <h2 className="error-card__title">Retrieve Failed</h2>
          <p className="error-card__desc">{error}</p>
          <button className="btn btn--primary" onClick={loadData}>
            Retry Load
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          
          {/* Keyword Search */}
          <div style={{ position: 'relative', flex: '1 1 240px', minWidth: '200px' }}>
            <Search style={{ position: 'absolute', top: '50%', left: '12px', transform: 'translateY(-50%)', width: '16px', height: '16px', color: '#94A3B8' }} />
            <input
              type="search"
              className="navbar__searchInput"
              style={{ width: '100%', paddingLeft: '36px', height: '38px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)' }}
              placeholder="Search user, ID or details..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setCurrentPage(1)
              }}
            />
          </div>

          {/* Action Filter */}
          <div style={{ flex: '0 1 180px', minWidth: '130px' }}>
            <select
              className="form-control"
              style={{ width: '100%', height: '38px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)', padding: '0 8px' }}
              value={selectedAction}
              onChange={(e) => {
                setSelectedAction(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">All Actions</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
              <option value="LOGIN">LOGIN</option>
              <option value="REGISTER">REGISTER</option>
            </select>
          </div>

          {/* Resource Filter */}
          <div style={{ flex: '0 1 180px', minWidth: '130px' }}>
            <select
              className="form-control"
              style={{ width: '100%', height: '38px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)', padding: '0 8px' }}
              value={selectedResource}
              onChange={(e) => {
                setSelectedResource(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">All Resources</option>
              <option value="Vehicle">Vehicle</option>
              <option value="Driver">Driver</option>
              <option value="Shipment">Shipment</option>
              <option value="Trip">Trip</option>
              <option value="User">User</option>
              <option value="FuelRecord">Fuel Record</option>
              <option value="Maintenance">Maintenance</option>
              <option value="DriverAssignment">Assignment</option>
              <option value="DriverAttendance">Attendance</option>
            </select>
          </div>

          {/* Reset Filters */}
          {(searchTerm || selectedAction || selectedResource) && (
            <button
              className="btn btn--secondary"
              style={{ height: '38px', display: 'flex', alignItems: 'center', gap: '8px' }}
              onClick={handleResetFilters}
            >
              <RotateCcw style={{ width: '14px', height: '14px' }} />
              <span>Clear</span>
            </button>
          )}

        </div>
      </div>

      {/* Logs Table DataGrid */}
      <div className="datagrid-container">
        <div className="datagrid-wrapper">
          <table className="datagrid">
            <thead>
              <tr>
                <th style={{ width: '100px' }}>Log ID</th>
                <th style={{ width: '120px' }}>Action</th>
                <th style={{ width: '150px' }}>Resource (ID)</th>
                <th>Details</th>
                <th style={{ width: '220px' }}>User Context</th>
                <th style={{ width: '180px' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {currentItems.length > 0 ? (
                currentItems.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>#LOG-{log.id}</td>
                    <td>
                      <span className={`badge ${getActionBadgeClass(log.action)}`} style={{ padding: '3px 8px', fontSize: '11px', fontWeight: 700 }}>
                        {log.action}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, fontSize: '13px' }}>{log.resource}</span>
                        {log.resource_id && (
                          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>ID: {log.resource_id}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: '13px', color: 'var(--text-main)', wordBreak: 'break-word', maxWeight: '400px' }}>
                        {log.details || '-'}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, fontSize: '13px' }}>{log.user_email || 'Anonymous'}</span>
                        {log.user_id && (
                          <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>User ID: #{log.user_id}</span>
                        )}
                      </div>
                    </td>
                    <td style={{ fontSize: '12.5px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {formatTimestamp(log.timestamp)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state" style={{ padding: '48px 0' }}>
                      <ClipboardList className="empty-state__icon" style={{ width: '48px', height: '48px', color: 'var(--text-secondary)' }} />
                      <p className="empty-state__title">No logs matching filters</p>
                      <p className="empty-state__desc">Try checking search keywords or filters.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="datagrid-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', borderTop: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Page {currentPage} of {totalPages} &bull; Showing {indexOfFirstItem + 1} to {Math.min(indexOfLastItem, filteredLogs.length)} of {filteredLogs.length} entries
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn--secondary" style={{ padding: '6px 12px' }} disabled={currentPage === 1} onClick={() => handlePageChange(currentPage - 1)}>
                <ChevronLeft style={{ width: '16px', height: '16px' }} />
                <span>Prev</span>
              </button>
              <button className="btn btn--secondary" style={{ padding: '6px 12px' }} disabled={currentPage === totalPages} onClick={() => handlePageChange(currentPage + 1)}>
                <span>Next</span>
                <ChevronRight style={{ width: '16px', height: '16px' }} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
