import { useEffect, useState } from 'react'
import { LayoutDashboard, TrendingUp, TrendingDown, Zap, Activity } from 'lucide-react'
import { marketApi, portfolioApi, simulatorApi } from '../api'
import {
  PieChart as RePieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, XAxis, YAxis,
} from 'recharts'

const COLORS = ['#d4af37','#f0cc55','#9a7b1e','#6b521a','#3b82f6','#22c55e']

const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n)

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState(null)
  const [pnl,       setPnl]       = useState(null)
  const [history,   setHistory]   = useState([])
  const [watchlist, setWatchlist] = useState([])
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    Promise.allSettled([
      portfolioApi.get().then(r => setPortfolio(r.data)),
      simulatorApi.pnl().then(r => setPnl(r.data)),
      portfolioApi.history().then(r => setHistory(r.data)),
      marketApi.watchlist().then(r => setWatchlist(r.data)),
    ]).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="page loading-center">
      <div className="spinner" />
      <p>Loading your dashboard…</p>
    </div>
  )

  const totalReal = portfolio?.total_current_value || 0
  const simValue  = pnl?.total_account_value || 100000
  const realPnl   = portfolio?.overall_gain_loss || 0

  return (
    <main className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Your investment overview at a glance</p>
      </div>

      {/* Stat cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Real Portfolio</div>
          <div className="stat-value">{fmt(totalReal)}</div>
          <div className={`stat-change ${realPnl >= 0 ? 'positive' : 'negative'}`}>
            {realPnl >= 0 ? '▲' : '▼'} {fmt(Math.abs(realPnl))} ({portfolio?.overall_gain_loss_pct?.toFixed(2) || 0}%)
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Simulator Account</div>
          <div className="stat-value">{fmt(simValue)}</div>
          <div className={`stat-change ${(pnl?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
            Unrealized: {fmt(pnl?.unrealized_pnl || 0)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Virtual Balance</div>
          <div className="stat-value">{fmt(pnl?.wallet_balance || 100000)}</div>
          <div className="stat-change text-muted">Cash available</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Holdings</div>
          <div className="stat-value">{portfolio?.assets?.length || 0}</div>
          <div className="stat-change text-muted">Real assets tracked</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Allocation Pie */}
        <div className="card">
          <div className="card-header">
            <Activity size={16} className="text-gold" />
            <span className="card-title">Asset Allocation</span>
          </div>
          {portfolio?.allocation?.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <RePieChart>
                <Pie data={portfolio.allocation} dataKey="value_inr" nameKey="asset_type"
                  cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={3}>
                  {portfolio.allocation.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                  formatter={(val) => fmt(val)}
                />
              </RePieChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-center" style={{ minHeight: 220 }}>
              <p className="text-muted">No real assets yet. Add via Portfolio →</p>
            </div>
          )}
          {portfolio?.allocation?.map((a, i) => (
            <div key={a.asset_type} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginTop: '0.25rem' }}>
              <span style={{ color: COLORS[i % COLORS.length] }}>● {a.asset_type}</span>
              <span className="text-muted">{a.percentage}%</span>
            </div>
          ))}
        </div>

        {/* Portfolio history */}
        <div className="card">
          <div className="card-header">
            <TrendingUp size={16} className="text-gold" />
            <span className="card-title">Portfolio Value History</span>
          </div>
          {history.length > 1 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={history}>
                <CartesianGrid stroke="rgba(212,175,55,0.07)" />
                <XAxis dataKey="snapshot_date" tick={{ fontSize: 10, fill: '#7a7670' }} />
                <YAxis tick={{ fontSize: 10, fill: '#7a7670' }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' }}
                  formatter={(v) => fmt(v)}
                />
                <Line type="monotone" dataKey="total_value_inr" stroke="var(--gold)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-center" style={{ minHeight: 220 }}>
              <p className="text-muted">Take a snapshot to start tracking history</p>
            </div>
          )}
        </div>
      </div>

      {/* Live Watchlist */}
      <div className="card">
        <div className="card-header">
          <Activity size={16} className="text-gold" />
          <span className="card-title">Market Watchlist</span>
          <span className="badge badge-green" style={{ marginLeft: 'auto' }}>Live</span>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th className="text-right">Price</th>
                <th className="text-right">Change</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.length === 0 ? (
                <tr><td colSpan={5} className="text-center text-muted" style={{ padding: '2rem' }}>Loading market data…</td></tr>
              ) : watchlist.map(item => (
                <tr key={item.symbol}>
                  <td className="fw-700 text-gold">{item.symbol}</td>
                  <td className="text-muted" style={{ fontSize: '0.85rem' }}>{item.name}</td>
                  <td className="text-right fw-700">{fmt(item.price)}</td>
                  <td className={`text-right ${item.change_pct >= 0 ? 'positive' : 'negative'}`}>
                    {item.change_pct >= 0 ? '▲' : '▼'} {Math.abs(item.change_pct).toFixed(2)}%
                  </td>
                  <td><span className="badge badge-gold">{item.source}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
