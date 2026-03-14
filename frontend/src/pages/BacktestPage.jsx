import { useEffect, useState } from 'react'
import { BarChart2, Play, Clock } from 'lucide-react'
import { backtestApi } from '../api'
import toast from 'react-hot-toast'
import {
  LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'

const fmt  = n => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n)
const fmtP = n => `${n >= 0 ? '+' : ''}${n?.toFixed(2) || 0}%`

const STRATEGIES = [
  { value: 'sma_crossover',      label: '📈 SMA Crossover', desc: 'Buy when fast MA crosses above slow MA' },
  { value: 'rsi_mean_reversion', label: '📊 RSI Reversion', desc: 'Buy oversold, sell overbought' },
]

export default function BacktestPage() {
  const [history, setHistory] = useState([])
  const [result,  setResult]  = useState(null)
  const [running, setRunning] = useState(false)
  const [form, setForm] = useState({
    symbol: 'RELIANCE', strategy: 'sma_crossover',
    start_date: '2022-01-01', end_date: '2024-12-31',
    fast: 20, slow: 50, period: 14, oversold: 30, overbought: 70,
  })

  useEffect(() => {
    backtestApi.history().then(r => setHistory(r.data)).catch(() => {})
  }, [])

  const handle = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const run = async e => {
    e.preventDefault()
    setRunning(true); setResult(null)
    try {
      const params = form.strategy === 'sma_crossover'
        ? { fast: +form.fast, slow: +form.slow }
        : { period: +form.period, oversold: +form.oversold, overbought: +form.overbought }

      const res = await backtestApi.run({
        symbol: form.symbol, strategy: form.strategy,
        start_date: form.start_date, end_date: form.end_date, params,
      })
      setResult(res.data)
      backtestApi.history().then(r => setHistory(r.data))
      toast.success('Backtest complete!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Backtest failed')
    } finally { setRunning(false) }
  }

  const r = result?.result || {}

  return (
    <main className="page">
      <div className="page-header">
        <h1>Strategy Backtester</h1>
        <p>Test your trading strategies against 2+ years of historical data</p>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Config form */}
        <div className="card">
          <div className="card-header"><BarChart2 size={16} className="text-gold"/><span className="card-title">Strategy Configuration</span></div>
          <form onSubmit={run}>
            <div className="form-group">
              <label>Symbol</label>
              <input name="symbol" placeholder="RELIANCE, TCS, BTC" value={form.symbol} onChange={handle} required/>
            </div>
            <div className="grid-2" style={{gap:'0.75rem'}}>
              <div className="form-group">
                <label>Start Date</label>
                <input name="start_date" type="date" value={form.start_date} onChange={handle}/>
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input name="end_date" type="date" value={form.end_date} onChange={handle}/>
              </div>
            </div>
            <div className="form-group">
              <label>Strategy</label>
              <div style={{display:'flex',flexDirection:'column',gap:'0.5rem',marginTop:'0.25rem'}}>
                {STRATEGIES.map(s => (
                  <label key={s.value} style={{
                    display:'flex',gap:'0.75rem',padding:'0.75rem',cursor:'pointer',
                    borderRadius:'var(--radius-md)',border:`1px solid ${form.strategy===s.value?'var(--gold)':'var(--border)'}`,
                    background: form.strategy===s.value?'var(--gold-glow)':'var(--surface-2)',
                    transition:'all 0.2s'
                  }}>
                    <input type="radio" name="strategy" value={s.value} hidden checked={form.strategy===s.value} onChange={handle}/>
                    <div>
                      <div style={{fontWeight:600,fontSize:'0.88rem'}}>{s.label}</div>
                      <div style={{fontSize:'0.75rem',color:'var(--text-muted)'}}>{s.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            {form.strategy==='sma_crossover' && (
              <div className="grid-2" style={{gap:'0.75rem'}}>
                <div className="form-group"><label>Fast MA Days</label><input name="fast" type="number" value={form.fast} onChange={handle}/></div>
                <div className="form-group"><label>Slow MA Days</label><input name="slow" type="number" value={form.slow} onChange={handle}/></div>
              </div>
            )}
            {form.strategy==='rsi_mean_reversion' && (
              <div className="grid-2" style={{gap:'0.75rem'}}>
                <div className="form-group"><label>RSI Period</label><input name="period" type="number" value={form.period} onChange={handle}/></div>
                <div className="form-group"><label>Oversold</label><input name="oversold" type="number" value={form.oversold} onChange={handle}/></div>
                <div className="form-group"><label>Overbought</label><input name="overbought" type="number" value={form.overbought} onChange={handle}/></div>
              </div>
            )}
            <button type="submit" className="btn btn-gold btn-lg" style={{width:'100%'}} disabled={running}>
              {running ? <><span className="spinner-sm"/>Running simulation…</> : <><Play size={16}/>Run Backtest</>}
            </button>
          </form>
        </div>

        {/* Results metrics */}
        <div>
          {result ? (
            <>
              <div className="stats-grid" style={{gridTemplateColumns:'1fr 1fr',marginBottom:'1rem'}}>
                <div className="stat-card">
                  <div className="stat-label">Final Value</div>
                  <div className="stat-value text-gold">{fmt(r.final_value||0)}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Total Return</div>
                  <div className={`stat-value ${(r.total_return_pct||0)>=0?'positive':'negative'}`}>{fmtP(r.total_return_pct)}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">CAGR</div>
                  <div className={`stat-value ${(r.cagr_pct||0)>=0?'positive':'negative'}`}>{fmtP(r.cagr_pct)}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Sharpe Ratio</div>
                  <div className="stat-value">{r.sharpe_ratio?.toFixed(3)||'—'}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Max Drawdown</div>
                  <div className="stat-value negative">{fmtP(-(r.max_drawdown_pct||0))}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Win Rate</div>
                  <div className="stat-value positive">{fmtP(r.win_rate_pct)}</div>
                  <div className="stat-change text-muted">{r.total_trades||0} total trades</div>
                </div>
              </div>
              <div className="card">
                <div className="card-header"><span className="card-title">Equity Curve</span></div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={r.equity_curve||[]}>
                    <CartesianGrid stroke="rgba(212,175,55,0.07)"/>
                    <XAxis dataKey="date" tick={{fontSize:9,fill:'#7a7670'}} interval="preserveStartEnd"/>
                    <YAxis tick={{fontSize:9,fill:'#7a7670'}} tickFormatter={v=>`₹${(v/1000).toFixed(0)}k`}/>
                    <Tooltip contentStyle={{background:'var(--surface-2)',border:'1px solid var(--border)',color:'var(--text)'}} formatter={v=>fmt(v)}/>
                    <Line type="monotone" dataKey="value" stroke="var(--gold)" strokeWidth={2} dot={false}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="card loading-center" style={{minHeight:400}}>
              <BarChart2 size={40} style={{opacity:0.2}}/>
              <p className="text-muted">Configure and run a backtest to see results</p>
            </div>
          )}
        </div>
      </div>

      {/* History */}
      <div className="card">
        <div className="card-header"><Clock size={16} className="text-gold"/><span className="card-title">Past Backtests</span></div>
        <div className="table-wrapper">
          <table>
            <thead><tr><th>Symbol</th><th>Strategy</th><th>Status</th><th>Run At</th></tr></thead>
            <tbody>
              {!history.length ? (
                <tr><td colSpan={4} className="text-center text-muted" style={{padding:'1.5rem'}}>No backtests yet</td></tr>
              ) : history.map(j => (
                <tr key={j.id}>
                  <td className="fw-700">{j.symbol}</td>
                  <td><span className="badge badge-blue">{j.strategy}</span></td>
                  <td><span className={`badge ${j.status==='done'?'badge-green':'badge-red'}`}>{j.status}</span></td>
                  <td className="text-muted" style={{fontSize:'0.8rem'}}>{new Date(j.created_at).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
