import { Routes, Route, Outlet } from "react-router-dom"
import Layout from "./components/Layout"
import Home from "./pages/Home"
import Pricing from "./pages/Pricing"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import Chat from "./pages/Chat"
import Quadrant from "./pages/Quadrant"
import { DashboardDataProvider } from "./context/DashboardDataContext"
import { AuthProvider } from "./context/AuthContext"
import { useAuth } from "./hooks/useAuth"
import RequireAuth from "./components/RequireAuth"

function DashboardArea() {
  const { session } = useAuth()
  return (
    <DashboardDataProvider hotelSlug={session.hotelSlug}>
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
          <Route element={<RequireAuth />}>
            <Route element={<DashboardArea />}>
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
            </Route>
          </Route>
          <Route path="quadrant" element={<Quadrant />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
