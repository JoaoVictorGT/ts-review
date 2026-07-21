import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { Mail, Lock } from "lucide-react"
import Logo from "../components/Logo"
import { useAuth } from "../hooks/useAuth"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  async function handleSubmit(event) {
    event.preventDefault()
    if (submitting) return
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate("/dashboard")
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="min-h-[640px] grid md:grid-cols-2">
      <div className="relative bg-slate-900 hidden md:flex flex-col justify-between p-12 overflow-hidden">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, #38bdf8 0%, transparent 40%), radial-gradient(circle at 80% 70%, #2563eb 0%, transparent 45%)",
          }}
        />
        <div className="relative">
          <Logo light />
        </div>
        <div className="relative">
          <p className="text-2xl text-white leading-snug max-w-sm">
            Access the world's largest hotel intelligence platform.
          </p>
          <p className="text-sm text-blue-200 mt-4">Verified reviews. Trusted stays.</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-10">
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold text-slate-900 mb-1">Welcome back</h1>
          <p className="text-sm text-slate-500 mb-8">Sign in to access your reports.</p>
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm px-3 py-2">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="text-xs font-medium text-slate-600">
                Corporate email
              </label>
              <div className="mt-1 relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="text-xs font-medium text-slate-600">
                Password
              </label>
              <div className="mt-1 relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-gradient-to-r from-sky-400 to-blue-600 text-white text-sm font-medium rounded-lg py-2.5 shadow-sm hover:shadow-md transition-shadow disabled:opacity-50"
            >
              {submitting ? "Signing in..." : "Sign in"}
            </button>
            <p className="text-sm text-slate-500 text-center">
              No account yet?{" "}
              <Link to="/register" className="text-blue-600 hover:text-blue-800 font-medium">
                Create one
              </Link>
            </p>
          </div>
        </form>
      </div>
    </section>
  )
}
