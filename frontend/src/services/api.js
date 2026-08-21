import axios from 'axios'

// Public API origin. Empty string = same origin (used by Docker/Nginx).
// Local Vite: set VITE_API_URL=http://127.0.0.1:8000 in frontend/.env
export const API_BASE_URL = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  ''
).replace(/\/$/, '')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fleetflow_token')

  if (token) {
    if (typeof config.headers?.set === 'function') {
      config.headers.set('Authorization', `Bearer ${token}`)
    } else {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      // Token expired or invalid — clear stored auth and redirect to login
      localStorage.removeItem('fleetflow_token')
      localStorage.removeItem('fleetflow_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export const authService = {
  login(payload) {
    return api.post('/auth/login', payload)
  },
  register(payload) {
    return api.post('/auth/register', payload)
  },
  logout() {
    clearStoredAuth()
  },
}

export function clearStoredAuth() {
  localStorage.removeItem('fleetflow_token')
  localStorage.removeItem('fleetflow_user')
}

export const driverService = {
  getAll() {
    return api.get('/drivers/')
  },
  getById(id) {
    return api.get(`/drivers/${id}`)
  },
  create(payload) {
    return api.post('/drivers/', payload)
  },
  update(id, payload) {
    return api.put(`/drivers/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/drivers/${id}`)
  },
}

export const vehicleService = {
  getAll() {
    return api.get('/vehicles/')
  },
  getById(id) {
    return api.get(`/vehicles/${id}`)
  },
  create(payload) {
    return api.post('/vehicles/', payload)
  },
  update(id, payload) {
    return api.put(`/vehicles/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/vehicles/${id}`)
  },
}

export const shipmentService = {
  getAll() {
    return api.get('/shipments/')
  },
  getById(id) {
    return api.get(`/shipments/${id}`)
  },
  create(payload) {
    return api.post('/shipments/', payload)
  },
  update(id, payload) {
    return api.put(`/shipments/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/shipments/${id}`)
  },
  getTrackingStatus(trackingNumber) {
    return api.get(`/shipments/${encodeURIComponent(trackingNumber)}/status`)
  },
}

export const fuelRecordService = {
  getAll() {
    return api.get('/fuel-records/')
  },
  getById(id) {
    return api.get(`/fuel-records/${id}`)
  },
  create(payload) {
    return api.post('/fuel-records/', payload)
  },
  update(id, payload) {
    return api.put(`/fuel-records/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/fuel-records/${id}`)
  },
  getAnalytics() {
    return api.get('/analytics/fuel')
  },
}

export const maintenanceService = {
  getAll() {
    return api.get('/maintenance/')
  },
  getById(id) {
    return api.get(`/maintenance/${id}`)
  },
  getByVehicle(vehicleId) {
    return api.get(`/maintenance/vehicle/${vehicleId}`)
  },
  getByVehicleRecord(vehicleId, maintenanceId) {
    return api.get(`/maintenance/vehicle/${vehicleId}/${maintenanceId}`)
  },
  create(payload) {
    return api.post('/maintenance/', payload)
  },
  update(id, payload) {
    return api.put(`/maintenance/${id}`, payload)
  },
  cancel(id) {
    return api.patch(`/maintenance/${id}/cancel`)
  },
}

export const driverAssignmentService = {
  getAll() {
    return api.get('/driver-assignments/')
  },
  getById(id) {
    return api.get(`/driver-assignments/${id}`)
  },
  create(payload) {
    return api.post('/driver-assignments/', payload)
  },
  update(id, payload) {
    return api.put(`/driver-assignments/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/driver-assignments/${id}`)
  },
}

export const driverAttendanceService = {
  getAll() {
    return api.get('/driver-attendance/')
  },
  getById(id) {
    return api.get(`/driver-attendance/${id}`)
  },
  create(payload) {
    return api.post('/driver-attendance/', payload)
  },
  update(id, payload) {
    return api.put(`/driver-attendance/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/driver-attendance/${id}`)
  },
}

export const driverPerformanceService = {
  getByDriverId(driverId) {
    return api.get(`/drivers/${driverId}/performance`)
  },
}

export const analyticsService = {
  getOperations() {
    return api.get('/analytics/operations')
  },
}

export const dashboardService = {
  getSummary() {
    return api.get('/dashboard/summary')
  },
  getFleet() {
    return api.get('/dashboard/fleet')
  },
}

export const tripService = {
  getAll() {
    return api.get('/trips/')
  },
  getById(id) {
    return api.get(`/trips/${id}`)
  },
  create(payload) {
    return api.post('/trips/', payload)
  },
  update(id, payload) {
    return api.put(`/trips/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/trips/${id}`)
  },
  getRoute(id) {
    return api.get(`/trips/${id}/route`)
  },
  getEta(id) {
    return api.get(`/trips/${id}/eta`)
  },
}

export const userService = {
  getAll() {
    return api.get('/users/')
  },
  update(id, payload) {
    return api.put(`/users/${id}`, payload)
  },
  remove(id) {
    return api.delete(`/users/${id}`)
  },
}

export const auditLogService = {
  getAll(params) {
    return api.get('/audit-logs/', { params })
  },
}




export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('fleetflow_token', token)
    return
  }

  localStorage.removeItem('fleetflow_token')
}

export function getAuthToken() {
  return localStorage.getItem('fleetflow_token')
}

export function getStoredUser() {
  const rawUser = localStorage.getItem('fleetflow_user')

  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser)
  } catch {
    return null
  }
}

export function setStoredUser(user) {
  if (user) {
    localStorage.setItem('fleetflow_user', JSON.stringify(user))
    return
  }

  localStorage.removeItem('fleetflow_user')
}

export function getApiErrorMessage(error, fallbackMessage = 'Request failed.') {
  const detail = error?.response?.data?.detail || error?.response?.data?.message || fallbackMessage

  return Array.isArray(detail) ? detail[0] : detail
}

export default api