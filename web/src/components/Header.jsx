import { Link, NavLink } from "react-router-dom"
import Logo from "./Logo"
import { useAuth } from "../hooks/useAuth"

const LINKS = [
  { to: "/", label: "Methodology" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/chat", label: "Chat" },
  { to: "/quadrant", label: "Quadrant" },
  { to: "/pricing", label: "Pricing" },
]

export default function Header() {
  const { session, logout } = useAuth()

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/">
          <Logo />
        </Link>
        <nav className="hidden md:flex items-center gap-8">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `text-sm transition-colors ${
                  isActive ? "text-blue-600 font-medium" : "text-slate-600 hover:text-blue-600"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        {session ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{session.hotelName}</span>
            <button
              type="button"
              onClick={logout}
              className="text-sm font-medium text-blue-600 border border-blue-200 rounded-lg px-4 py-2 hover:bg-blue-50 transition-colors"
            >
              Log out
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 border border-blue-200 rounded-lg px-4 py-2 hover:bg-blue-50 transition-colors"
          >
            Log in
          </Link>
        )}
      </div>
    </header>
  )
}
