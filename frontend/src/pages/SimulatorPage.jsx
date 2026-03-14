import { useEffect, useState } from 'react'
import { Zap, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import { simulatorApi } from '../api'
import toast from 'react-hot-toast'

const fmt = n => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:2}).format(n)

const ASSET_TYPES = ['stock','crypto','gold','mutual_fund']

export default function SimulatorPage() {
  const [pnl,     setPnl]     = useState(null)
  const [orders,  setOrders]  = useState([])
  const [loading, setLoading] = useState(true)
  const [placing, setPlacing] = useState(false)
  const [form,    setForm]    = useState({ symbol: '', asset_type: 'stock', order_type: 'buy', quantity: '' })

  const load = async () => {
    try {
      const [p, o] = await Promise.all([simulatorApi.pnl(), simulatorApi.orders()])
      setPnl(p.data); setOrders(o.data)
    } catch { toast.error('Error loading simulator') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleChange = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const placeOrder = async e => {
    e.preventDefault()
    if (!form.symbol || !form.quantity) { toast.error('Fill all fields'); return }
    setPlacing(true)
    try {
      const res = await simulatorApi.placeOrder({
        symbol: form.symbol, asset_type: form.asset_type,
        order_type: form.order_type, quantity: parseFloat(form.quantity)
      })
      toast.success(`${form.order_type.toUpperCase()} order filled @ ${fmt(res.data.price_at_execution)}`)
      setForm(p => ({ ...p, symbol:'', quantity:'' }))
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Order failed')
    } finally { setPlacing(false) }
  }

  const reset = async () => {
    if (!window.confirm('Reset your virtual wallet to ₹1,00,000?')) return
    await simulatorApi.reset()
    toast.success('Wallet reset!')
    load()
  }

  if (loading) return <div className="page loading-center"><div className="spinner"/></div>

  return (
    <main className="page">
      <div className="page-header flex-between" style={{ flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <h1>Virtual Simulator</h1>
          <p>Practice trading with ₹1,00,000 virtual money — zero risk!</p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={reset}><RefreshCw size={14}/>Reset Wallet</button>
      </div>

      {/* P&L Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Wallet Balance</div>
          <div className="stat-value">{fmt(pnl?.wallet_balance||100000)}</div>
          <div className="stat-change text-muted">Cash in hand</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Portfolio Value</div>
          <div className="stat-value">{fmt(pnl?.current_portfolio_value||0)}</div>
          <div className="stat-change text-muted">Virtual holdings</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Account</div>
          <div className="stat-value text-gold">{fmt(pnl?.total_account_value||100000)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Unrealized P&L</div>
          <div className={`stat-value ${(pnl?.unrealized_pnl||0)>=0?'positive':'negative'}`}>
            {fmt(pnl?.unrealized_pnl||0)}
          </div>
          <div className={`stat-change ${(pnl?.unrealized_pnl||0)>=0?'positive':'negative'}`}>
            {(pnl?.unrealized_pnl_pct||0).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Order form */}
        <div className="card">
          <div className="card-header"><Zap size={16} className="text-gold"/><span className="card-title">Place Order</span></div>
          <form onSubmit={placeOrder}>
            <div className="form-group">
              <label>Asset Type</label>
              <select name="asset_type" value={form.asset_type} onChange={handleChange}>
                {ASSET_TYPES.map(t=><option key={t} value={t}>{t.replace('_',' ').toUpperCase()}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Symbol</label>
              <input name="symbol" placeholder={form.asset_type==='crypto'?'BTC, ETH, SOL':'RELIANCE, TCS, INFY'} value={form.symbol} onChange={handleChange} required/>
            </div>
            <div className="form-group">
              <label>Quantity</label>
              <input name="quantity" type="number" step="any" min="0.00001" placeholder="1" value={form.quantity} onChange={handleChange} required/>
            </div>
            <div className="form-group">
              <label>Order Type</label>
              <div className="flex gap-1">
                {['buy','sell'].map(t => (
                  <label key={t} style={{
                    flex:1, display:'flex', alignItems:'center', justifyContent:'center',
                    padding:'0.6rem', cursor:'pointer', borderRadius:'var(--radius-md)',
                    border:`1px solid ${form.order_type===t?(t==='buy'?'var(--green)':'var(--red)'):'var(--border)'}`,
                    background: form.order_type===t?(t==='buy'?'rgba(34,197,94,0.12)':'rgba(239,68,68,0.12)'):'transparent',
                    color: form.order_type===t?(t==='buy'?'var(--green)':'var(--red)'):'var(--text-muted)',
                    fontWeight:600, fontSize:'0.85rem', transition:'all 0.2s',
                  }}>
                    <input type="radio" name="order_type" value={t} hidden checked={form.order_type===t} onChange={handleChange}/>
                    {t==='buy'?<TrendingUp size={14} style={{marginRight:'0.4rem'}}/>:<TrendingDown size={14} style={{marginRight:'0.4rem'}}/>}
                    {t.toUpperCase()}
                  </label>
                ))}
              </div>
            </div>
            <button type="submit" className={`btn btn-lg`} disabled={placing}
              style={{
                width:'100%',
                background: form.order_type==='buy'?'linear-gradient(135deg,#22c55e,#16a34a)':'linear-gradient(135deg,#ef4444,#dc2626)',
                color:'#fff'
              }}>
              {placing ? 'Executing…' : `${form.order_type.toUpperCase()} at Market Price`}
            </button>
          </form>
        </div>

        {/* Holdings */}
        <div className="card">
          <div className="card-header"><span className="card-title">Virtual Holdings</span></div>
          <div className="table-wrapper" style={{ maxHeight: 320, overflowY:'auto' }}>
            <table>
              <thead>
                <tr><th>Symbol</th><th className="text-right">Qty</th><th className="text-right">Avg Cost</th><th className="text-right">P&L</th></tr>
              </thead>
              <tbody>
                {!pnl?.holdings?.length ? (
                  <tr><td colSpan={4} className="text-center text-muted" style={{padding:'1.5rem'}}>No holdings yet</td></tr>
                ) : pnl.holdings.map(h => (
                  <tr key={h.symbol}>
                    <td className="fw-700">{h.symbol}</td>
                    <td className="text-right font-mono">{h.quantity}</td>
                    <td className="text-right">{fmt(h.avg_cost_inr)}</td>
                    <td className={`text-right ${h.unrealized_pnl>=0?'positive':'negative'}`}>
                      {fmt(h.unrealized_pnl)}<br/>
                      <span style={{fontSize:'0.72rem'}}>{h.unrealized_pnl_pct?.toFixed(2)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Order History */}
      <div className="card">
        <div className="card-header"><span className="card-title">Order History</span></div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>Symbol</th><th>Type</th><th className="text-right">Qty</th><th className="text-right">Price</th><th className="text-right">Total</th><th>Time</th></tr>
            </thead>
            <tbody>
              {!orders.length ? (
                <tr><td colSpan={6} className="text-center text-muted" style={{padding:'2rem'}}>No orders yet</td></tr>
              ) : orders.map(o => (
                <tr key={o.id}>
                  <td className="fw-700">{o.symbol}</td>
                  <td><span className={`badge ${o.order_type==='buy'?'badge-green':'badge-red'}`}>{o.order_type.toUpperCase()}</span></td>
                  <td className="text-right font-mono">{o.quantity}</td>
                  <td className="text-right">{fmt(o.price_at_execution)}</td>
                  <td className="text-right fw-700">{fmt(o.total_value)}</td>
                  <td className="text-muted" style={{fontSize:'0.8rem'}}>{new Date(o.executed_at).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
