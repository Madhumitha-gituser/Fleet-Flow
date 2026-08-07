import { NavLink, useNavigate } from "react-router-dom";
import { clearStoredAuth } from "../services/api";
import { 
  LayoutDashboard, 
  Users, 
  Truck, 
  Package, 
  Wrench, 
  BarChart3, 
  BarChart2,
  User, 
  LogOut,
  Shield,
  Compass,
  Search,
  Fuel,
  ClipboardList,
  Route
} from "lucide-react";

const navigationItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Admin", "Fleet Manager"] },
  { to: "/users", label: "Users", icon: Shield, roles: ["Admin"] },
  { to: "/drivers", label: "Drivers", icon: Users, roles: ["Admin", "Fleet Manager"] },
  { to: "/vehicles", label: "Vehicles", icon: Truck, roles: ["Admin", "Fleet Manager"] },
  { to: "/shipments", label: "Shipments", icon: Package, roles: ["Admin", "Dispatcher"] },
  { to: "/tracking", label: "Track Cargo", icon: Search, roles: ["Admin", "Fleet Manager", "Dispatcher", "Driver"] },
  { to: "/trips", label: "Trips", icon: Compass, roles: ["Admin", "Dispatcher", "Driver"] },
  { to: "/maintenance", label: "Maintenance", icon: Wrench, roles: ["Admin", "Fleet Manager"] },
  { to: "/operations", label: "Driver Ops", icon: Users, roles: ["Admin", "Fleet Manager"] },
  { to: "/fuel-records", label: "Fuel Records", icon: Fuel, roles: ["Admin", "Fleet Manager", "Dispatcher", "Driver"] },
  { to: "/reports", label: "Reports", icon: BarChart3, roles: ["Admin", "Fleet Manager"] },
  { to: "/analytics", label: "Fleet Analytics", icon: BarChart2, roles: ["Admin", "Fleet Manager"] },
  { to: "/audit-logs", label: "Audit Logs", icon: ClipboardList, roles: ["Admin", "Fleet Manager"] },
  { to: "/profile", label: "Profile", icon: User, roles: ["Admin", "Fleet Manager", "Dispatcher", "Driver"] },
];


export default function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearStoredAuth();
    navigate("/login", { replace: true });
  };

  const storedUser = localStorage.getItem('fleetflow_user');
  let role = 'Fleet Manager';
  if (storedUser) {
    try {
      const parsedUser = JSON.parse(storedUser);
      role = parsedUser?.role || 'Fleet Manager';
    } catch (e) {
      // ignore
    }
  }

  const visibleItems = navigationItems.filter(item => item.roles.includes(role));

  return (
    <div className="sidebar" aria-label="Primary navigation">
      {/* Brand Header */}
      <div className="sidebar__brand">
        <div className="sidebar__logo-container" aria-hidden="true">
          <Route className="sidebar__logo-svg" />
        </div>
        <div className="sidebar__brandText">
          <h1 className="sidebar__title">FleetFlow</h1>
          <p className="sidebar__subtitle">Fleet Management Platform</p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar__nav">
        <ul className="sidebar__list">
          {visibleItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <li key={item.to} className="sidebar__item">
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `sidebar__link${isActive ? " sidebar__link--active" : ""}`
                  }
                >
                  <IconComponent className="sidebar__icon" aria-hidden="true" />
                  <span className="sidebar__label">{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Sidebar Footer Logout */}
      <div className="sidebar__footer">
        <button
          type="button"
          className="sidebar__logout"
          onClick={handleLogout}
        >
          <LogOut className="sidebar__icon" aria-hidden="true" />
          <span className="sidebar__label">Logout</span>
        </button>
      </div>
    </div>
  );
}

