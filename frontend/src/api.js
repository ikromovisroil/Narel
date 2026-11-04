// Backend bilan ishlash. Tokenlar localStorage'da saqlanadi.
import { getLang, t } from './i18n'

export const SHOP_NAME = 'Narel'

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

// Refresh token har safar yangilanadi (eskisi serverda bekor qilinadi). Bir vaqtda bir nechta so'rov 401 olsa,
// yangilash bitta bo'ladi — aks holda ikkinchisi bekor qilingan token bilan urinib, foydalanuvchini chiqarib yuborardi.
let refreshing = null
function refreshAccess() {
  if (!tokens.refresh) return Promise.resolve(false)
  refreshing ??= (async () => {
    try {
      const r = await fetch('/api/auth/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: tokens.refresh }),
      })
      if (!r.ok) { tokens.clear(); return false }
      const d = await r.json()
      tokens.set(d.access, d.refresh)
      return true
    } catch {
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

// Chiqish: refresh token serverda bekor qilinadi (o'g'irlangan bo'lsa ham ishlamaydi)
export function revokeTokens() {
  const refresh = tokens.refresh
  tokens.clear()
  if (refresh) {
    fetch('/api/auth/logout/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh }),
    }).catch(() => {})
  }
}

export async function api(path, { method = 'GET', body, auth = true } = {}, retried = false) {
  const headers = { 'Content-Type': 'application/json', 'Accept-Language': getLang() }
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
  if (!d) return t("Server bilan bog'lanib bo'lmadi")
  if (typeof d === 'string') return d
  if (d.detail) return d.detail
  return Object.values(d).flat().map(v => (typeof v === 'object' ? JSON.stringify(v) : v)).join(' ')
}

// Raqam guruhlari orasida bo'linmas bo'sh joy: "23 700 000" ikki qatorga bo'linmaydi,
// kerak bo'lsa faqat "so'm" keyingi qatorga o'tadi
const NBSP = '\u00A0'
export const formatPrice = n =>
  `${String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, NBSP)} ${t("so'm")}`
