import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Activity, AlertTriangle, BarChart2, PieChartIcon, TrendingUp } from 'lucide-react'
import api, { analyticsService, getApiErrorMessage, maintenanceService } from '../services/api'

const PALETTE = {
  blue: '#2563EB',
  green: '#16A34A',
  amber: '#D97706',
  red: '#DC2626',
  violet: '#7C3AED',
  cyan: '#0891B2',
  slate: '#64748B',
}

const STATUS_COLORS_VEHICLE = [PALETTE.green, PALETTE.blue, PALETTE.amber, PALETTE.red]
const STATUS_COLORS_SHIPMENT = [PALETTE.green, PALETTE.blue, PALETTE.amber, PALETTE.red, PALETTE.slate]
const STATUS_COLORS_DRIVER = [PALETTE.green, PALETTE.amber, PALETTE.violet, PALETTE.slate]
const MAINTENANCE_COLORS = [PALETTE.blue, PALETTE.green, PALETTE.amber, PALETTE.red, PALETTE.violet, PALETTE.cyan]

function ChartCard({ title, icon: Icon, iconColor, children, minHeight = 280 }) {
  return (
    <div className="card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid var(--border-color)', paddingBottom: '14px' }}>
        <Icon style={{ width: '18px', height: '18px', color: iconColor || 'var(--primary)' }} />
        <h3 style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>{title}</h3>
      </div>
      <div style={{ minHeight, width: '100%' }}>{children}</div>
    </div>
  )
}

function EmptyChart({ message = 'No data available yet' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 200, gap: '8px', color: 'var(--text-secondary)' }}>
      <BarChart2 style={{ width: '36px', height: '36px', opacity: 0.3 }} />
      <p style={{ fontSize: '13px' }}>{message}</p>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px 14px', fontSize: '12px', boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}>
        {label && <p style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--text-main)' }}>{label}</p>}
        {payload.map((entry, i) => (
          <p key={i} style={{ color: entry.color || 'var(--text-main)', marginTop: '2px' }}>
            {entry.name}: <strong>{entry.value}</strong>
          </p>
        ))}
      </div>
    )
  }
  return null
}

const CustomPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null
  const RADIAN = Math.PI / 180
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight={700}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

export default function FleetAnalytics() {
  const [vehicles, setVehicles] = useState([])
  const [shipments, setShipments] = useState([])
  const [drivers, setDrivers] = useState([])
  const [maintenance, setMaintenance] = useState([])
  const [fuelRecords, setFuelRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    try {
      setLoading(true)
      setError('')
      const [vehiclesRes, shipmentsRes, driversRes, maintenanceRes, fuelRes] = await Promise.all([
        api.get('/vehicles/'),
        api.get('/shipments/'),
        api.get('/drivers/'),
        maintenanceService.getAll(),
        api.get('/fuel-records/').catch(() => ({ data: [] })),
      ])
      setVehicles(vehiclesRes.data || [])
      setShipments(shipmentsRes.data || [])
      setDrivers(driversRes.data || [])
      setMaintenance(maintenanceRes.data || [])
      setFuelRecords(fuelRes.data || [])
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load analytics data.'))
    } finally {
      setLoading(false)
    }
  }

  // — Vehicle status pie data
  const vehicleStatusMap = vehicles.reduce((acc, v) => {
    const key = v.status || 'Unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const vehiclePieData = Object.entries(vehicleStatusMap).map(([name, value]) => ({ name, value }))

  // — Shipment status bar data
  const shipmentStatusMap = shipments.reduce((acc, s) => {
    const key = s.current_status || 'Unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const shipmentBarData = Object.entries(shipmentStatusMap).map(([name, value]) => ({ name, value }))

  // — Driver status donut data
  const driverStatusMap = drivers.reduce((acc, d) => {
    const key = d.status || 'Unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const driverPieData = Object.entries(driverStatusMap).map(([name, value]) => ({ name, value }))

  // — Maintenance by category bar data
  const maintCategoryMap = maintenance.reduce((acc, m) => {
    const key = m.category || 'Other'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  const maintBarData = Object.entries(maintCategoryMap).map(([name, value]) => ({ name, value }))

  // — Fuel trend by date (Area chart) - group by month
  const fuelTrendMap = fuelRecords.reduce((acc, f) => {
    if (!f.fuel_date) return acc
    const month = f.fuel_date.slice(0, 7) // "YYYY-MM"
    if (!acc[month]) acc[month] = { month, quantity: 0, cost: 0 }
    acc[month].quantity += Number(f.fuel_quantity || 0)
    acc[month].cost += Number(f.fuel_cost || 0)
    return acc
  }, {})
  const fuelTrendData = Object.values(fuelTrendMap).sort((a, b) => a.month.localeCompare(b.month))

  // — Monthly shipments trend
  const shipmentMonthMap = shipments.reduce((acc, s) => {
    const dateStr = s.created_at || s.pickup_date || ''
    if (!dateStr) return acc
    const month = dateStr.slice(0, 7)
    if (!acc[month]) acc[month] = { month, total: 0, delivered: 0 }
    acc[month].total += 1
    if ((s.current_status || '').toLowerCase() === 'delivered') acc[month].delivered += 1
    return acc
  }, {})
  const shipmentTrendData = Object.values(shipmentMonthMap).sort((a, b) => a.month.localeCompare(b.month))

  // KPI summary
  const totalVehicles = vehicles.length
  const activeVehicles = vehicles.filter(v => (v.status || '').toLowerCase() === 'available').length
  const totalDrivers = drivers.length
  const totalShipments = shipments.length
  const deliveredShipments = shipments.filter(s => (s.current_status || '').toLowerCase() === 'delivered').length

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '60vh' }}>
        <div className="loading-spinner"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-card">
        <AlertTriangle className="error-card__icon" />
        <h2 className="error-card__title">Analytics Load Failed</h2>
        <p className="error-card__desc">{error}</p>
        <button className="btn btn--primary" onClick={loadAll} style={{ marginTop: '12px' }}>Retry</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div>
        <h1 className="page-title">Fleet Analytics</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
          Live operational dashboards — fleet status, shipment trends, fuel consumption, and driver performance.
        </p>
      </div>

      {/* KPI Summary Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {[
          { label: 'Total Vehicles', value: totalVehicles, color: '#EFF6FF', text: PALETTE.blue },
          { label: 'Active Vehicles', value: activeVehicles, color: '#F0FDF4', text: PALETTE.green },
          { label: 'Total Drivers', value: totalDrivers, color: '#FFF7ED', text: PALETTE.amber },
          { label: 'Total Shipments', value: totalShipments, color: '#F5F3FF', text: PALETTE.violet },
          { label: 'Delivered', value: deliveredShipments, color: '#ECFDF5', text: '#059669' },
        ].map(({ label, value, color, text }) => (
          <div key={label} className="kpi-card" style={{ '--kpi-accent': text }}>
            <div className="kpi-card__icon-container" style={{ backgroundColor: color, color: text }}>
              <Activity className="kpi-card__icon" />
            </div>
            <div className="kpi-card__details">
              <span className="kpi-card__label">{label}</span>
              <span className="kpi-card__value">{value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Row 1: Vehicle Status Pie + Driver Status Donut */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>

        {/* Vehicle Status Pie Chart */}
        <ChartCard title="Fleet Vehicle Status" icon={PieChartIcon} iconColor={PALETTE.blue}>
          {vehiclePieData.length === 0 ? <EmptyChart message="No vehicles registered yet" /> : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={vehiclePieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={50}
                  dataKey="value"
                  labelLine={false}
                  label={CustomPieLabel}
                >
                  {vehiclePieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS_VEHICLE[index % STATUS_COLORS_VEHICLE.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value) => <span style={{ fontSize: '12px', color: 'var(--text-main)' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Driver Status Donut */}
        <ChartCard title="Driver Availability Status" icon={PieChartIcon} iconColor={PALETTE.green}>
          {driverPieData.length === 0 ? <EmptyChart message="No drivers registered yet" /> : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={driverPieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={55}
                  dataKey="value"
                  labelLine={false}
                  label={CustomPieLabel}
                >
                  {driverPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS_DRIVER[index % STATUS_COLORS_DRIVER.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend formatter={(value) => <span style={{ fontSize: '12px', color: 'var(--text-main)' }}>{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Row 2: Shipment Status Bar + Maintenance Category Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>

        {/* Shipment Status Bar Chart */}
        <ChartCard title="Shipment Status Breakdown" icon={BarChart2} iconColor={PALETTE.amber}>
          {shipmentBarData.length === 0 ? <EmptyChart message="No shipments yet" /> : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={shipmentBarData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Shipments" radius={[4, 4, 0, 0]}>
                  {shipmentBarData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS_SHIPMENT[index % STATUS_COLORS_SHIPMENT.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Maintenance Category Bar Chart */}
        <ChartCard title="Maintenance by Category" icon={BarChart2} iconColor={PALETTE.red}>
          {maintBarData.length === 0 ? <EmptyChart message="No maintenance records yet" /> : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={maintBarData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                  {maintBarData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={MAINTENANCE_COLORS[index % MAINTENANCE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Row 3: Fuel Trend Area Chart (full width) */}
      <ChartCard title="Fuel Consumption Trend (Monthly)" icon={TrendingUp} iconColor={PALETTE.cyan} minHeight={300}>
        {fuelTrendData.length === 0 ? <EmptyChart message="No fuel records to show trend" /> : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={fuelTrendData} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="fuelQuantityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={PALETTE.blue} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={PALETTE.blue} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="fuelCostGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={PALETTE.amber} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={PALETTE.amber} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(value) => <span style={{ fontSize: '12px', color: 'var(--text-main)' }}>{value}</span>} />
              <Area
                type="monotone"
                dataKey="quantity"
                name="Fuel Quantity (L)"
                stroke={PALETTE.blue}
                strokeWidth={2.5}
                fill="url(#fuelQuantityGradient)"
                dot={{ r: 4, fill: PALETTE.blue }}
                activeDot={{ r: 6 }}
              />
              <Area
                type="monotone"
                dataKey="cost"
                name="Fuel Cost (₹)"
                stroke={PALETTE.amber}
                strokeWidth={2.5}
                fill="url(#fuelCostGradient)"
                dot={{ r: 4, fill: PALETTE.amber }}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {/* Row 4: Monthly Shipment Trend (full width) */}
      <ChartCard title="Monthly Shipment Performance" icon={TrendingUp} iconColor={PALETTE.green} minHeight={300}>
        {shipmentTrendData.length === 0 ? <EmptyChart message="No shipment data to show trend" /> : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={shipmentTrendData} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(value) => <span style={{ fontSize: '12px', color: 'var(--text-main)' }}>{value}</span>} />
              <Line type="monotone" dataKey="total" name="Total Shipments" stroke={PALETTE.blue} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="delivered" name="Delivered" stroke={PALETTE.green} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  )
}
