import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import BacktestPage from './pages/BacktestPage'
import AIAdvisorPage from './pages/AIAdvisorPage'

function ProtectedRoute({ element }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="flex-center" style={{ minHeight: '100vh' }}>
      <div className="spinner" />
    </div>
  )
  return user ? element : <Navigate to="/login" replace />
}

function AppShell() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Routes>
          <Route path="/"          element={<DashboardPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/backtest"  element={<BacktestPage />} />
          <Route path="/ai"        element={<AIAdvisorPage />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/*"        element={<ProtectedRoute element={<AppShell />} />} />
      </Routes>
    </AuthProvider>
  )
}
