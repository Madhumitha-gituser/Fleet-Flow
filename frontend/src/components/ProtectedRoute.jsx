import { Navigate, Outlet } from 'react-router-dom'
import { getStoredUser } from '../services/api'
import { hasAllowedRole } from '../utils/roles'

export default function ProtectedRoute({ allowedRoles }) {
  const token = localStorage.getItem('fleetflow_token')

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles) {
    const user = getStoredUser()
    if (!hasAllowedRole(user?.role, allowedRoles)) {
      return <Navigate to="/403" replace />
    }
  }

  return <Outlet />
}