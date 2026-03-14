import { useEffect, useState } from 'react'
import { Plus, Trash2, RefreshCw, PieChart } from 'lucide-react'
import { portfolioApi } from '../api'
import toast from 'react-hot-toast'
import {
  PieChart as RePieChart, Pie, Cell, Tooltip, ResponsiveContainer
} from 'recharts'

const ASSET_TYPES = ['stock','crypto','gold','mutual_fund','fixed_deposit','other']
const COLORS = ['#d4af37','#f0cc55','#9a7b1e','#3b82f6','#22c55e','#f97316']
const fmt = n => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n)

const empty = { asset_type: 'stock', symbol: '', name: '', quantity: '', purchase_price: '', notes: '' }

export default function PortfolioPage() {
  const [data,    setData]    = useState(null)
  const [form,    setForm]    = useState(empty)
  const [showForm,setShowForm]= useState(false)
  const [loading, setLoading] = useState(true)
  const [saving,  setSaving]  = useState(false)

  const load = () => portfolioApi.get()
    .then(r => setData(r.data))
    .catch(() => toast.error('Failed to load portfolio'))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleChange = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    setSaving(true)
    try {
      await portfolioApi.add({
        ...form,
        quantity: parseFloat(form.quantity),
        purchase_price: parseFloat(form.purchase_price) || 0,
      })
      toast.success('Asset added!')
      setForm(empty); setShowForm(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add asset')
    } finally { setSaving(false) }
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this asset?')) return
    await portfolioApi.remove(id)
    toast.success('Asset deleted')
    load()
  }

  const snap = async () => {
    await portfolioApi.snapshot()
    toast.success('Snapshot saved ✅')
  }

  if (loading) return <div className="page loading-center"><div className="spinner" /></div>

  return (
    <main className="page">
      <div className="page-header flex-between" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Real Portfolio</h1>
          <p>Track your actual investments with live valuations</p>
        </div>
        <div className="flex gap-1">
          <button className="btn btn-ghost btn-sm" onClick={snap}><RefreshCw size={14}/>Snapshot</button>
          <button className="btn btn-gold" onClick={() => setShowForm(p => !p)}>
            <Plus size={16}/> Add Asset
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)' }}>
        <div className="stat-card">
          <div className="stat-label">Total Invested</div>
          <div className="stat-value">{fmt(data?.total_invested||0)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Current Value</div>
          <div className="stat-value text-gold">{fmt(data?.total_current_value||0)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Overall P&L</div>
          <div className={`stat-value ${(data?.overall_gain_loss||0)>=0?'positive':'negative'}`}>
            {fmt(data?.overall_gain_loss||0)}
          </div>
          <div className={`stat-change ${(data?.overall_gain_loss||0)>=0?'positive':'negative'}`}>
            {data?.overall_gain_loss_pct?.toFixed(2)||0}%
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Add form */}
        {showForm && (
          <div className="card">
            <div className="card-header"><Plus size={16} className="text-gold" /><span className="card-title">Add New Asset</span></div>
            <form onSubmit={submit}>
              <div className="grid-2" style={{ gap: '0.75rem' }}>
                <div className="form-group">
                  <label>Asset Type</label>
                  <select name="asset_type" value={form.asset_type} onChange={handleChange}>
                    {ASSET_TYPES.map(t => <option key={t} value={t}>{t.replace('_',' ').toUpperCase()}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Symbol / ID</label>
                  <input name="symbol" placeholder="RELIANCE / bitcoin" value={form.symbol} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label>Name</label>
                  <input name="name" placeholder="Display name" value={form.name} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label>Quantity / Units</label>
                  <input name="quantity" type="number" step="any" placeholder="10" value={form.quantity} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label>Purchase Price (₹)</label>
                  <input name="purchase_price" type="number" step="any" placeholder="0" value={form.purchase_price} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <input name="notes" placeholder="Optional notes" value={form.notes} onChange={handleChange} />
                </div>
              </div>
              <div className="flex gap-1 mt-2">
                <button type="submit" className="btn btn-gold" disabled={saving}>{saving?'Saving…':'Add Asset'}</button>
                <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        )}

        {/* Allocation chart */}
        {data?.allocation?.length > 0 && (
          <div className="card">
            <div className="card-header"><PieChart size={16} className="text-gold"/><span className="card-title">Allocation</span></div>
            <ResponsiveContainer width="100%" height={200}>
              <RePieChart>
                <Pie data={data.allocation} dataKey="value_inr" nameKey="asset_type" cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={2}>
                  {data.allocation.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                </Pie>
                <Tooltip contentStyle={{background:'var(--surface-2)',border:'1px solid var(--border)',color:'var(--text)'}} formatter={v=>fmt(v)}/>
              </RePieChart>
            </ResponsiveContainer>
            {data.allocation.map((a,i)=>(
              <div key={a.asset_type} className="flex-between" style={{fontSize:'0.8rem',marginTop:'0.3rem'}}>
                <span style={{color:COLORS[i%COLORS.length]}}>● {a.asset_type}</span>
                <span className="text-muted">{a.percentage}% · {fmt(a.value_inr)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assets Table */}
      <div className="card">
        <div className="card-header"><span className="card-title">Holdings</span></div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Asset</th><th>Type</th><th className="text-right">Qty</th>
                <th className="text-right">Avg Cost</th><th className="text-right">Live Price</th>
                <th className="text-right">Current Value</th><th className="text-right">P&L</th><th></th>
              </tr>
            </thead>
            <tbody>
              {!data?.assets?.length ? (
                <tr><td colSpan={8} className="text-center text-muted" style={{padding:'2rem'}}>No assets yet. Add your first holding!</td></tr>
              ) : data.assets.map(a => (
                <tr key={a.id}>
                  <td>
                    <div className="fw-700">{a.symbol}</div>
                    <div style={{fontSize:'0.75rem',color:'var(--text-muted)'}}>{a.name}</div>
                  </td>
                  <td><span className="badge badge-gold">{a.asset_type}</span></td>
                  <td className="text-right font-mono">{a.quantity}</td>
                  <td className="text-right">{fmt(a.purchase_price)}</td>
                  <td className="text-right text-gold fw-700">{fmt(a.live_price||0)}</td>
                  <td className="text-right fw-700">{fmt(a.current_value||0)}</td>
                  <td className={`text-right ${(a.gain_loss||0)>=0?'positive':'negative'}`}>
                    {fmt(a.gain_loss||0)}<br/>
                    <span style={{fontSize:'0.75rem'}}>{(a.gain_loss_pct||0).toFixed(2)}%</span>
                  </td>
                  <td>
                    <button className="btn btn-danger btn-sm" onClick={() => remove(a.id)}>
                      <Trash2 size={13}/>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
