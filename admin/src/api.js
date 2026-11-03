// Admin panel uchun backend bilan ishlash
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
  if (!r.ok) return false
  tokens.set((await r.json()).access)
  return true
}

function query(params) {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, v)
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export async function api(path, { method = 'GET', body, params } = {}, retried = false) {
  const headers = {}
  let payload
  if (body instanceof FormData) payload = body
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (tokens.access) headers.Authorization = `Bearer ${tokens.access}`

  const r = await fetch(`/api${path}${query(params)}`, { method, headers, body: payload })
  if (r.status === 401 && !retried) {
    if (await refreshAccess()) return api(path, { method, body, params }, true)
    tokens.clear()
    window.dispatchEvent(new Event('auth-expired'))
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
  return Object.entries(d)
    .map(([k, v]) => `${k === 'non_field_errors' ? '' : k + ': '}${[].concat(v).join(' ')}`)
    .join('\n')
}

// Backend xatolarini antd Form maydonlariga joylash
export function applyFormErrors(form, err) {
  const d = err?.data
  if (!d || typeof d !== 'object' || d.detail) return false
  const known = Object.keys(form.getFieldsValue(true))
  const fields = Object.entries(d)
    .filter(([k]) => known.includes(k))
    .map(([name, errors]) => ({ name, errors: [].concat(errors).map(String) }))
  form.setFields(fields)
  return fields.length > 0
}

export const upload = (path, file) => {
  const fd = new FormData()
  fd.append('file', file)
  return api(path, { method: 'POST', body: fd })
}
