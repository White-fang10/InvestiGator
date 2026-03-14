import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, PieChart, Zap, BarChart2, Brain,
  LogOut, ChevronRight, TrendingUp
} from 'lucide-react'
import './Sidebar.css'

const NAV = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard'  },
  { to: '/portfolio', icon: PieChart,         label: 'Portfolio'  },
  { to: '/simulator', icon: Zap,              label: 'Simulator'  },
  { to: '/backtest',  icon: BarChart2,        label: 'Backtest'   },
  { to: '/ai',        icon: Brain,            label: 'AI Advisor' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <img src="/logo.png" alt="InvestiGator" className="logo-img" />
        <div className="logo-text">
          <span className="logo-name">Invest<span className="logo-accent">iGator</span></span>
          <span className="logo-sub">Smart Investing</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={18} className="nav-icon" />
            <span className="nav-label">{label}</span>
            <ChevronRight size={14} className="nav-arrow" />
          </NavLink>
        ))}
      </nav>

      {/* Market ticker teaser */}
      <div className="sidebar-ticker">
        <TrendingUp size={12} />
        <span>Live markets active</span>
      </div>

      {/* User */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="user-avatar">
            {user?.profile?.display_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="user-info">
            <span className="user-name">{user?.profile?.display_name || 'Investor'}</span>
            <span className="user-email">{user?.email}</span>
          </div>
        </div>
        <button className="logout-btn" onClick={handleLogout} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  )
}
