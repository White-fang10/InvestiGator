import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'
import './Auth.css'

const RISK_OPTIONS = [
  { value: 'conservative', label: '🛡️ Conservative', desc: 'Low risk, stable returns' },
  { value: 'moderate',     label: '⚖️ Moderate',     desc: 'Balanced growth & safety' },
  { value: 'aggressive',   label: '🚀 Aggressive',   desc: 'High risk, high reward' },
]

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    display_name: '', email: '', password: '', risk_tolerance: 'moderate'
  })
  const [loading, setLoading] = useState(false)

  const handle = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    if (form.password.length < 8) { toast.error('Password must be at least 8 characters'); return }
    setLoading(true)
    try {
      await register(form)
      toast.success('Account created! Welcome 🐊')
      navigate('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-bg">
        <div className="auth-orb orb-1" />
        <div className="auth-orb orb-2" />
      </div>

      <div className="auth-card auth-card-wide">
        <div className="auth-logo">
          <img src="/logo.png" alt="InvestiGator" />
          <h1>Invest<span>iGator</span></h1>
        </div>

        <div className="auth-divider" />

        <form onSubmit={submit} className="auth-form">
          <h2>Create Account</h2>
          <p className="auth-sub">Start your investment journey</p>

          <div className="form-group">
            <label htmlFor="display_name">Display Name</label>
            <input id="display_name" name="display_name" type="text" placeholder="Your name"
              value={form.display_name} onChange={handle} required />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" placeholder="investor@example.com"
              value={form.email} onChange={handle} required />
          </div>

          <div className="form-group">
            <label htmlFor="reg-password">Password</label>
            <input id="reg-password" name="password" type="password" placeholder="Min 8 characters"
              value={form.password} onChange={handle} required />
          </div>

          <div className="form-group">
            <label>Risk Tolerance</label>
            <div className="risk-grid">
              {RISK_OPTIONS.map(opt => (
                <label key={opt.value}
                  className={`risk-card ${form.risk_tolerance === opt.value ? 'selected' : ''}`}
                >
                  <input type="radio" name="risk_tolerance" value={opt.value}
                    checked={form.risk_tolerance === opt.value} onChange={handle} hidden />
                  <span className="risk-label">{opt.label}</span>
                  <span className="risk-desc">{opt.desc}</span>
                </label>
              ))}
            </div>
          </div>

          <button type="submit" className="btn btn-gold btn-lg" style={{ width: '100%' }} disabled={loading}>
            {loading ? <span className="spinner-sm" /> : <UserPlus size={18} />}
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <Link to="/login">Sign in →</Link>
        </p>
      </div>
    </div>
  )
}
