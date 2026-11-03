// Backend bilan ishlash. Tokenlar localStorage'da saqlanadi.
export const SHOP_NAME = 'TechShop'

const tokens = {
  get access() { return localStorage.getItem('access') },
  get refresh() { return localStorage.getItem('refresh') },
  set(access, refresh) {
    localStorage.setItem('access', access)
    if (refresh) localStorage.setItem('refresh', refresh)
  },
  clear() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
  },
}
export { tokens }

async function refreshAccess() {
  if (!tokens.refresh) return false
  const r = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: tokens.refresh }),
  })
  if (!r.ok) { tokens.clear(); return false }
  tokens.set((await r.json()).access)
  return true
}

export async function api(path, { method = 'GET', body, auth = true } = {}, retried = false) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && tokens.access) headers.Authorization = `Bearer ${tokens.access}`
  const r = await fetch(`/api${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  })
  if (r.status === 401 && auth && !retried && (await refreshAccess())) {
    return api(path, { method, body, auth }, true)
  }
  const data = r.status === 204 ? null : await r.json().catch(() => null)
  if (!r.ok) throw { status: r.status, data }
  return data
}

export function errorText(err) {
  const d = err?.data
  if (!d) return 'Server bilan bog\'lanib bo\'lmadi'
  if (typeof d === 'string') return d
  if (d.detail) return d.detail
  return Object.values(d).flat().map(v => (typeof v === 'object' ? JSON.stringify(v) : v)).join(' ')
}

export const formatPrice = n =>
  `${String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} so'm`
