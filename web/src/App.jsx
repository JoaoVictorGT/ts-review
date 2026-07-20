import { Routes, Route, Outlet } from "react-router-dom"
import Layout from "./components/Layout"
import Home from "./pages/Home"
import Pricing from "./pages/Pricing"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Dashboard from "./pages/Dashboard"
import Quadrant from "./pages/Quadrant"
import { DashboardDataProvider } from "./context/DashboardDataContext"
import { AuthProvider } from "./context/AuthContext"
import { useAuth } from "./hooks/useAuth"
import RequireAuth from "./components/RequireAuth"

function DashboardArea() {
  const { session } = useAuth()
  return (
    <DashboardDataProvider token={session.token}>
      <Outlet />
    </DashboardDataProvider>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="pricing" element={<Pricing />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route element={<RequireAuth />}>
            <Route element={<DashboardArea />}>
              <Route path="dashboard" element={<Dashboard />} />
            </Route>
          </Route>
          <Route path="quadrant" element={<Quadrant />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
