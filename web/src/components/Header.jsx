import { Link, NavLink } from "react-router-dom"
import Logo from "./Logo"
import { useAuth } from "../hooks/useAuth"

export const LOGGED_OUT_LINKS = [
  { to: "/", label: "Methodology" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/pricing", label: "Pricing" },
]

export const LOGGED_IN_LINKS = [
  { to: "/", label: "Methodology" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/quadrant", label: "Quadrant" },
]

export default function Header() {
  const { session, logout } = useAuth()
  const links = session ? LOGGED_IN_LINKS : LOGGED_OUT_LINKS

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/">
          <Logo />
        </Link>
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => (
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
            {/* TODO: integrate checkout when payment API is ready */}
            <button
              type="button"
              disabled
              title="Coming soon — payment integration isn't live yet"
              className="text-xs font-medium text-white bg-gradient-to-r from-sky-400 to-blue-600 rounded-full px-4 py-1.5 opacity-60 cursor-not-allowed"
            >
              Upgrade
            </button>
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
