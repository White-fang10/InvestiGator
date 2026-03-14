import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        const { data } = await axios.post('/api/auth/refresh', { refresh_token: refresh })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  refresh:  (data) => api.post('/auth/refresh', data),
}

// ── Profile ───────────────────────────────────────────
export const profileApi = {
  me:     ()     => api.get('/profile/me'),
  update: (data) => api.patch('/profile/me', data),
}

// ── Market data ────────────────────────────────────────
export const marketApi = {
  price:     (symbol, assetType = 'stock') => api.get(`/market/price/${symbol}`, { params: { asset_type: assetType } }),
  prices:    (symbols, assetType = 'stock') => api.get('/market/prices', { params: { symbols, asset_type: assetType } }),
  watchlist: () => api.get('/market/watchlist'),
}

// ── Portfolio ──────────────────────────────────────────
export const portfolioApi = {
  get:      ()         => api.get('/portfolio/'),
  add:      (data)     => api.post('/portfolio/', data),
  update:   (id, data) => api.put(`/portfolio/${id}`, data),
  remove:   (id)       => api.delete(`/portfolio/${id}`),
  history:  ()         => api.get('/portfolio/history'),
  snapshot: ()         => api.post('/portfolio/snapshot'),
}

// ── Simulator ─────────────────────────────────────────
export const simulatorApi = {
  wallet:    ()       => api.get('/simulator/wallet'),
  placeOrder:(data)   => api.post('/simulator/orders', data),
  orders:    ()       => api.get('/simulator/orders'),
  pnl:       ()       => api.get('/simulator/pnl'),
  reset:     ()       => api.post('/simulator/reset'),
}

// ── Backtest ──────────────────────────────────────────
export const backtestApi = {
  run:     (data) => api.post('/backtest/run', data),
  history: ()     => api.get('/backtest/history'),
  get:     (id)   => api.get(`/backtest/${id}`),
}

// ── AI ─────────────────────────────────────────────────
export const aiApi = {
  health: ()  => api.get('/ai/health'),
  report: ()  => api.get('/ai/risk-report'),
}

export default api
