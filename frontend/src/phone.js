// Telefon: yozilayotganda "+998 90 123 45 67" ko'rinishiga keltiriladi
export function formatPhone(value) {
  let d = String(value || '').replace(/\D/g, '')
  if (d.startsWith('998')) d = d.slice(3)
  d = d.slice(0, 9)
  const parts = [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean)
  return ['+998', ...parts].join(' ')
}

export const phoneDigits = value => String(value || '').replace(/\D/g, '').replace(/^998/, '')
export const phoneOk = value => phoneDigits(value).length === 9

// Backend xatolarini maydonlar bo'yicha ajratadi: {field: "matn"}
export function fieldErrorsOf(err, fields) {
  const d = err?.data || {}
  const out = {}
  for (const f of fields) if (d[f]) out[f] = [].concat(d[f])[0]
  return out
}
