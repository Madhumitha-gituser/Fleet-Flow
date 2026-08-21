export function normalizeRole(role) {
  return String(role || '')
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
}

export function hasAllowedRole(userRole, allowedRoles = []) {
  const current = normalizeRole(userRole)
  return allowedRoles.some((role) => normalizeRole(role) === current)
}
