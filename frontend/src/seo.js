// Qidiruv tizimlari va ijtimoiy tarmoqlar uchun sahifa ma'lumotlari: sarlavha, tavsif, rasm,
// kanonik manzil va Google uchun tuzilgan ma'lumot (JSON-LD). Sahifadan chiqilganda standartga qaytadi.
import { useEffect } from 'react'

export const SITE_NAME = 'Rendershop'
const DEFAULT_TITLE = 'Rendershop — elektronika va maishiy texnika'
const DEFAULT_DESC = "Rendershop internet-do'koni: noutbuklar, smartfonlar, kompyuter qismlari va maishiy texnika. "
  + "Toshkent bo'ylab yetkazib berish, naqd va karta orqali to'lov."

function setMeta(attr, key, value) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', value)
}

function setCanonical(href) {
  let el = document.head.querySelector('link[rel="canonical"]')
  if (!el) {
    el = document.createElement('link')
    el.rel = 'canonical'
    document.head.appendChild(el)
  }
  el.href = href
}

function setJsonLd(data) {
  document.getElementById('seo-jsonld')?.remove()
  if (!data) return
  const el = document.createElement('script')
  el.type = 'application/ld+json'
  el.id = 'seo-jsonld'
  el.textContent = JSON.stringify(data)
  document.head.appendChild(el)
}

const clean = s => (s || '').replace(/\s+/g, ' ').trim()
export const shorten = (s, n = 160) => { const c = clean(s); return c.length > n ? c.slice(0, n - 1).trimEnd() + '…' : c }
export const absUrl = src => (!src ? '' : /^https?:/.test(src) ? src : window.location.origin + src)

function apply({ title, description, image, path, jsonLd, noindex }) {
  const full = title ? `${title} — ${SITE_NAME}` : DEFAULT_TITLE
  const desc = shorten(description) || DEFAULT_DESC
  const url = window.location.origin + (path ?? window.location.pathname)
  document.title = full
  setMeta('name', 'description', desc)
  setMeta('name', 'robots', noindex ? 'noindex, follow' : 'index, follow')
  setMeta('property', 'og:title', full)
  setMeta('property', 'og:description', desc)
  setMeta('property', 'og:url', url)
  setMeta('property', 'og:image', absUrl(image) || window.location.origin + '/icon-512.png')
  setMeta('property', 'og:type', jsonLd?.['@type'] === 'Product' ? 'product' : 'website')
  setCanonical(url)
  setJsonLd(jsonLd)
}

// seo === null — ma'lumot hali yuklanmagan, hech narsa o'zgartirilmaydi
export function useSeo(seo) {
  const key = seo ? JSON.stringify(seo) : null
  useEffect(() => {
    if (key === null) return
    apply(JSON.parse(key))
  }, [key])
  useEffect(() => () => apply({}), [])
}
