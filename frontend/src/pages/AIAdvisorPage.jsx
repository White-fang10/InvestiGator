import { useState, useEffect } from 'react'
import { Brain, AlertTriangle, Lightbulb, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { aiApi } from '../api'
import toast from 'react-hot-toast'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

const LEVEL_COLORS = { Low: '#22c55e', Moderate: '#f97316', High: '#ef4444', 'Very High': '#dc2626' }

export default function AIAdvisorPage() {
  const [report,   setReport]   = useState(null)
  const [health,   setHealth]   = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    aiApi.health()
      .then(r => setHealth(r.data))
      .catch(() => setHealth({ ollama_available: false }))
      .finally(() => setChecking(false))
  }, [])

  const generate = async () => {
    setLoading(true); setReport(null)
    try {
      const r = await aiApi.report()
      setReport(r.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not generate report')
    } finally { setLoading(false) }
  }

  const gaugeData = report ? [
    { name: 'Risk', value: report.risk_score, fill: LEVEL_COLORS[report.level] || '#ef4444' }
  ] : []

  return (
    <main className="page">
      <div className="page-header">
        <h1>AI Risk Advisor</h1>
        <p>Powered by DeepSeek R1 running locally — your data stays on your device</p>
      </div>

      {/* Ollama health badge */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <div className="flex-between flex-wrap" style={{ gap: '1rem' }}>
          <div className="flex items-center gap-2">
            {checking ? (
              <span className="text-muted">Checking AI status…</span>
            ) : health?.ollama_available ? (
              <><Wifi size={16} style={{ color: 'var(--green)' }} /><span style={{ color: 'var(--green)', fontWeight: 600 }}>DeepSeek R1 · Online</span></>
            ) : (
              <><WifiOff size={16} style={{ color: 'var(--red)' }} /><span style={{ color: 'var(--red)', fontWeight: 600 }}>Ollama not detected — using rule-based fallback</span></>
            )}
          </div>
          <button className="btn btn-gold" onClick={generate} disabled={loading}>
            {loading ? <><span className="spinner-sm" /> Analyzing with AI…</> : <><Brain size={16} /> Generate Risk Report</>}
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading-center" style={{ minHeight: 300 }}>
          <div className="spinner pulse-gold" />
          <p className="text-muted">DeepSeek is analyzing your portfolio…<br/><small>This may take 10–30 seconds</small></p>
        </div>
      )}

      {report && !loading && (
        <>
          {/* Risk Score Gauge + Summary */}
          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <div className="card-header" style={{ width: '100%' }}>
                <Brain size={16} className="text-gold" />
                <span className="card-title">Risk Score</span>
              </div>
              <div style={{ position: 'relative', width: 200, height: 200 }}>
                <ResponsiveContainer width={200} height={200}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%"
                    startAngle={225} endAngle={-45} data={[{ name:'bg', value:100, fill:'var(--surface-3)' }, ...gaugeData]}>
                    <RadialBar dataKey="value" cornerRadius={8} background={false} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div style={{
                  position: 'absolute', top: '50%', left: '50%',
                  transform: 'translate(-50%,-50%)',
                  textAlign: 'center',
                }}>
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: '2.5rem', fontWeight: 800, color: LEVEL_COLORS[report.level] || '#fff', lineHeight: 1 }}>
                    {report.risk_score}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>out of 100</div>
                </div>
              </div>
              <span style={{
                padding: '0.3rem 1.2rem',
                borderRadius: '100px',
                background: `${LEVEL_COLORS[report.level]}22`,
                border: `1px solid ${LEVEL_COLORS[report.level]}`,
                color: LEVEL_COLORS[report.level],
                fontWeight: 700,
                fontSize: '0.9rem',
              }}>
                {report.level} Risk
              </span>

              {/* Allocation */}
              {Object.keys(report.concentration || {}).length > 0 && (
                <div style={{ width: '100%' }}>
                  <div className="text-muted" style={{ fontSize: '0.75rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Portfolio Mix</div>
                  {Object.entries(report.concentration).map(([type, pct]) => (
                    <div key={type} style={{ marginBottom: '0.5rem' }}>
                      <div className="flex-between" style={{ fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                        <span>{type}</span><span className="text-gold fw-700">{pct}%</span>
                      </div>
                      <div style={{ height: 4, background: 'var(--surface-3)', borderRadius: 2 }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg,var(--gold),var(--gold-dim))', borderRadius: 2, transition: 'width 0.5s' }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Summary */}
            <div className="card">
              <div className="card-header">
                <Brain size={16} className="text-gold" />
                <span className="card-title">AI Assessment</span>
                <span className="badge badge-gold" style={{ marginLeft: 'auto' }}>DeepSeek R1</span>
              </div>
              <div style={{
                background: 'var(--surface-2)', borderRadius: 'var(--radius-md)',
                padding: '1.25rem', borderLeft: '3px solid var(--gold)',
                fontStyle: 'italic', color: 'var(--text)', lineHeight: 1.7,
                fontSize: '0.92rem', marginBottom: '1rem',
              }}>
                {report.ai_summary}
              </div>

              {/* Warnings */}
              {report.warnings?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1 mb-2">
                    <AlertTriangle size={14} style={{ color: 'var(--red)' }} />
                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--red)' }}>Warnings</span>
                  </div>
                  {report.warnings.map((w, i) => (
                    <div key={i} style={{
                      padding: '0.65rem 0.9rem', marginBottom: '0.5rem',
                      background: 'rgba(239,68,68,0.08)',
                      border: '1px solid rgba(239,68,68,0.2)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.875rem',
                    }}>{w}</div>
                  ))}
                </div>
              )}

              {/* Tips */}
              {report.tips?.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <div className="flex items-center gap-1 mb-2">
                    <Lightbulb size={14} className="text-gold" />
                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--gold)' }}>Suggestions</span>
                  </div>
                  {report.tips.map((t, i) => (
                    <div key={i} style={{
                      padding: '0.65rem 0.9rem', marginBottom: '0.5rem',
                      background: 'rgba(212,175,55,0.06)',
                      border: '1px solid rgba(212,175,55,0.2)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.875rem',
                    }}>{t}</div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <button className="btn btn-outline btn-sm" onClick={generate} disabled={loading}>
              <RefreshCw size={13} /> Regenerate Report
            </button>
          </div>
        </>
      )}

      {!report && !loading && (
        <div className="card loading-center" style={{ minHeight: 350 }}>
          <Brain size={48} style={{ opacity: 0.15 }} />
          <p className="text-muted" style={{ maxWidth: 400, textAlign: 'center' }}>
            Click <strong>Generate Risk Report</strong> to get a personalized AI-powered analysis of your virtual trading portfolio.
          </p>
        </div>
      )}
    </main>
  )
}
