import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api, revokeTokens, tokens } from './api'
import { getLang, setLang, t } from './i18n'

const StoreContext = createContext(null)
export const useStore = () => useContext(StoreContext)

function useLocal(key, initial) {
  const [value, setValue] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key)) ?? initial } catch { return initial }
  })
  useEffect(() => { localStorage.setItem(key, JSON.stringify(value)) }, [key, value])
  return [value, setValue]
}

export function StoreProvider({ children }) {
  const [user, setUser] = useState(null)
  // Savat: [{ id, slug, name, price, image, stock, qty }]
  const [cart, setCart] = useLocal('cart', [])
  const [favorites, setFavorites] = useLocal('favorites', [])
  const [lang, setLangState] = useState(getLang())

  const changeLang = code => {
    setLang(code)
    setLangState(code)
  }

  useEffect(() => { document.title = t('Narel — elektronika va maishiy texnika') }, [lang])

  // Admin Sozlamalarda yoqilgan to'lov usullari (nomlari joriy tilda)
  const [paymentMethods, setPaymentMethods] = useState([])
  // Do'kon ma'lumotlari va yetkazib berish (telefon, manzil, yetkazish bor-yo'qligi)
  const [storeInfo, setStoreInfo] = useState(null)
  useEffect(() => {
    api('/payment-methods/', { auth: false }).then(setPaymentMethods).catch(() => setPaymentMethods([]))
    api('/store-settings/', { auth: false }).then(setStoreInfo).catch(() => {})
  }, [lang])
  // Muddatli to'lov yoqilgan bo'lsa — necha oyga; aks holda null (oylik narx ko'rsatilmaydi)
  const installmentMonths = paymentMethods.find(m => m.code === 'installment')?.months || null
  const monthly = price => (installmentMonths ? Number(price) / installmentMonths : null)

  useEffect(() => {
    if (tokens.access) api('/auth/me/').then(setUser).catch(() => tokens.clear())
  }, [])

  // Token qaytaradigan kirish (SMS kod, Google); javobda created: yangi hisob ochildimi
  const tokenLogin = useCallback(async (path, body) => {
    const r = await api(path, { method: 'POST', body, auth: false })
    tokens.set(r.access, r.refresh)
    setUser(await api('/auth/me/'))
    return r
  }, [])
  const googleLogin = useCallback(credential => tokenLogin('/auth/google/', { credential }), [tokenLogin])
  // Chiqishda savat va sevimlilar shu qurilmadan tozalanadi (serverda saqlanib qoladi)
  const logout = () => { revokeTokens(); setUser(null); setCart([]); setFavorites([]) }

  const addToCart = (p, qty = 1) => setCart(items => {
    const found = items.find(i => i.id === p.id)
    if (found) return items.map(i => i.id === p.id ? { ...i, qty: Math.min(i.qty + qty, p.stock) } : i)
    return [...items, { id: p.id, slug: p.slug, name: p.name, price: p.price, image: p.image, stock: p.stock, qty }]
  })
  const setQty = (id, qty) => setCart(items =>
    items.map(i => i.id === id ? { ...i, qty: Math.max(1, Math.min(qty, i.stock)) } : i))
  const removeFromCart = id => setCart(items => items.filter(i => i.id !== id))

  // Savatdagi nom, narx va ombordagi sonni serverdan yangilash (joriy tilda)
  const refreshCart = async () => {
    const fresh = await Promise.all(cart.map(i =>
      api(`/products/${i.slug}/`, { auth: false }).then(p => ({ id: i.id, p })).catch(err => ({ id: i.id, gone: err?.status === 404 }))))
    setCart(items => items.flatMap(i => {
      const f = fresh.find(x => x.id === i.id)
      if (!f) return [i]
      if (f.gone) return []  // mahsulot o'chirilgan yoki yashirilgan
      if (!f.p) return [i]  // tarmoq xatosi — eskisini qoldiramiz
      const { name, price, image, stock } = f.p
      return [{ ...i, name, price, image, stock, qty: Math.max(1, Math.min(i.qty, stock || 1)) }]
    }))
  }
  const clearCart = () => setCart([])

  // Sevimlilarda kartochka uchun kerakli maydonlargina saqlanadi
  const favoriteFields = p => ({
    id: p.id, slug: p.slug, name: p.name, price: p.price, old_price: p.old_price,
    discount_percent: p.discount_percent, monthly_price: p.monthly_price, stock: p.stock,
    image: p.image, is_hit: p.is_hit, is_new: p.is_new,
  })
  const isFavorite = id => favorites.some(f => f.id === id)
  const toggleFavorite = p => {
    const adding = !favorites.some(f => f.id === p.id)
    setFavorites(list => (adding ? [favoriteFields(p), ...list.filter(f => f.id !== p.id)] : list.filter(f => f.id !== p.id)))
    if (synced.current) {
      const req = adding
        ? api('/favorites/', { method: 'POST', body: { product: p.id } })
        : api(`/favorites/${p.id}/`, { method: 'DELETE' })
      req.catch(() => {})
    }
  }
  const clearFavorites = () => {
    if (synced.current) favorites.forEach(f => api(`/favorites/${f.id}/`, { method: 'DELETE' }).catch(() => {}))
    setFavorites([])
  }

  // Narx, ombor va nomni serverdan yangilash (joriy tilda); o'chirilganlari olib tashlanadi
  const refreshFavorites = async () => {
    const fresh = await Promise.all(favorites.map(f =>
      api(`/products/${f.slug}/`, { auth: false }).then(p => ({ id: f.id, p })).catch(err => ({ id: f.id, gone: err?.status === 404 }))))
    setFavorites(list => list.flatMap(f => {
      const x = fresh.find(r => r.id === f.id)
      if (!x) return [f]
      if (x.gone) return []
      return [x.p ? favoriteFields(x.p) : f]
    }))
  }

  // ---------- Server bilan sinxron (kirgan mijoz) ----------
  // Kirganda: qurilmadagilar serverdagilarga qo'shiladi, keyin har bir o'zgarish serverga yoziladi.
  // Shunda sayt va mobil ilovada sevimlilar va savat bir xil bo'ladi.
  const synced = useRef(false)
  const pushedCart = useRef('')
  const cartBody = items => items.map(i => ({ product: i.id, quantity: i.qty }))
  const cartFromServer = res => res.items.map(({ product: p, quantity }) => ({
    id: p.id, slug: p.slug, name: p.name, price: p.price, image: p.image, stock: p.stock, qty: quantity,
  }))

  useEffect(() => {
    if (!user) { synced.current = false; return }
    let alive = true
    Promise.all([
      api('/favorites/sync/', { method: 'POST', body: { products: favorites.map(f => f.id) } }),
      api('/cart/sync/', { method: 'POST', body: { items: cartBody(cart) } }),
    ]).then(([favs, serverCart]) => {
      if (!alive) return
      setFavorites(favs.map(favoriteFields))
      const items = cartFromServer(serverCart)
      pushedCart.current = JSON.stringify(cartBody(items))
      setCart(items)
      synced.current = true
    }).catch(() => {}) // tarmoq xatosi — qurilmadagisi bilan ishlashda davom etadi
    return () => { alive = false }
  }, [user?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!synced.current) return undefined
    const body = JSON.stringify(cartBody(cart))
    if (body === pushedCart.current) return undefined
    const timer = setTimeout(() => {
      pushedCart.current = body
      api('/cart/', { method: 'PUT', body: { items: cartBody(cart) } }).catch(() => { pushedCart.current = '' })
    }, 500)
    return () => clearTimeout(timer)
  }, [cart]) // eslint-disable-line react-hooks/exhaustive-deps

  // Savat belgisida turli tovarlar soni (dona emas)
  const cartCount = cart.length
  const cartTotal = cart.reduce((s, i) => s + i.qty * Number(i.price), 0)

  return (
    <StoreContext.Provider value={{
      user, setUser, tokenLogin, googleLogin, logout, lang, changeLang, paymentMethods, installmentMonths, monthly, storeInfo,
      cart, cartCount, cartTotal, addToCart, setQty, removeFromCart, clearCart, refreshCart,
      favorites, isFavorite, toggleFavorite, clearFavorites, refreshFavorites,
    }}>
      {children}
    </StoreContext.Provider>
  )
}
