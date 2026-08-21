import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Drivers from "./pages/Drivers";
import Vehicles from "./pages/Vehicles";
import Shipments from "./pages/Shipments";
import Maintenance from "./pages/Maintenance";
import DriverOperations from "./pages/DriverOperations";
import Reports from "./pages/Reports";
import FuelRecords from "./pages/FuelRecords";
import Profile from "./pages/Profile";
import Users from "./pages/Users";
import Trips from "./pages/Trips";
import Tracking from "./pages/Tracking";
import AccessDenied from "./pages/AccessDenied";
import FleetAnalytics from "./pages/FleetAnalytics";
import AuditLogs from "./pages/AuditLogs";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/403" element={<AccessDenied />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          {/* Admin and Fleet Manager */}
          <Route
            element={
              <ProtectedRoute allowedRoles={["admin", "fleet manager"]} />
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/vehicles" element={<Vehicles />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/operations" element={<DriverOperations />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/analytics" element={<FleetAnalytics />} />
            <Route path="/audit-logs" element={<AuditLogs />} />
          </Route>

          {/* Fuel Records */}
          <Route
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "fleet manager",
                  "dispatcher",
                  "driver",
                ]}
              />
            }
          >
            <Route path="/fuel-records" element={<FuelRecords />} />
          </Route>

          {/* Shipments */}
          <Route
            element={<ProtectedRoute allowedRoles={["admin", "dispatcher"]} />}
          >
            <Route path="/shipments" element={<Shipments />} />
          </Route>

          {/* Trips */}
          <Route
            element={
              <ProtectedRoute
                allowedRoles={["admin", "dispatcher", "driver"]}
              />
            }
          >
            <Route path="/trips" element={<Trips />} />
          </Route>

          {/* Tracking */}
          <Route path="/tracking" element={<Tracking />} />

          {/* Users - Admin only */}
          <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
            <Route path="/users" element={<Users />} />
          </Route>

          {/* Profile */}
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
