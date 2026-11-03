// Rasm talablari backenddan bir marta olinadi (/api/admin/image-rules/)
import { useEffect, useState } from 'react'
import { api } from './api'

let cache = null
let pending = null

function loadRules() {
  if (cache) return Promise.resolve(cache)
  pending ||= api('/admin/image-rules/').then(r => { cache = r; return r }).finally(() => { pending = null })
  return pending
}

export function useImageRule(key) {
  const [rules, setRules] = useState(cache)
  useEffect(() => {
    if (!cache) loadRules().then(setRules).catch(() => {})
  }, [])
  return rules?.[key] || null
}

export const ruleHint = rule => (rule ? [
  `Tavsiya: ${rule.recommended[0]}×${rule.recommended[1]} px`,
  `kamida ${rule.min[0]}×${rule.min[1]} px`,
  `nisbat ${rule.ratio[0]}:${rule.ratio[1]}`,
  `${rule.formats.join('/')}, ${rule.max_mb} MB gacha`,
].join(' · ') : '')

function readSize(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => { resolve([img.naturalWidth, img.naturalHeight]); URL.revokeObjectURL(url) }
    img.onerror = () => { reject(new Error('bad')); URL.revokeObjectURL(url) }
    img.src = url
  })
}

const EXT = { JPG: ['image/jpeg'], PNG: ['image/png'], WEBP: ['image/webp'] }

// Yuborishdan oldin tez tekshiruv. Xato bo'lsa matn qaytaradi, bo'lmasa null.
// Asosiy tekshiruv baribir backendda.
export async function checkImage(file, rule) {
  if (!rule) return null
  const allowed = rule.formats.flatMap(f => EXT[f] || [])
  if (!allowed.includes(file.type)) return `Faqat ${rule.formats.join(', ')} formatlari qabul qilinadi.`
  if (file.size > rule.max_mb * 1024 * 1024) {
    return `Fayl hajmi ${rule.max_mb} MB dan oshmasligi kerak (sizniki ${(file.size / 1024 / 1024).toFixed(1)} MB).`
  }
  let w, h
  try { [w, h] = await readSize(file) } catch { return 'Rasmni o\'qib bo\'lmadi.' }
  const rec = `${rule.recommended[0]}×${rule.recommended[1]} px`
  if (w < rule.min[0] || h < rule.min[1]) {
    return `Rasm juda kichik: kamida ${rule.min[0]}×${rule.min[1]} px kerak (sizniki ${w}×${h}). Tavsiya: ${rec}.`
  }
  if (w > rule.max_side || h > rule.max_side) {
    return `Rasm juda katta: tomonlari ${rule.max_side} px dan oshmasin (sizniki ${w}×${h}).`
  }
  const target = rule.ratio[0] / rule.ratio[1]
  if (Math.abs(w / h - target) / target > 0.1) {
    return `Rasm nisbati ${rule.ratio[0]}:${rule.ratio[1]} bo'lishi kerak (sizniki ${w}×${h}). Tavsiya: ${rec}.`
  }
  return null
}

export const acceptFor = rule =>
  (rule ? rule.formats.flatMap(f => EXT[f] || []).join(',') : 'image/*')
