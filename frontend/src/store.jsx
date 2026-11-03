import { createContext, useContext, useEffect, useState } from 'react'
import { api, tokens } from './api'
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

  useEffect(() => { document.title = t('TechShop — elektronika va maishiy texnika') }, [lang])

  // Admin Sozlamalarda yoqilgan to'lov usullari (nomlari joriy tilda)
  const [paymentMethods, setPaymentMethods] = useState([])
  useEffect(() => {
    api('/payment-methods/', { auth: false }).then(setPaymentMethods).catch(() => setPaymentMethods([]))
  }, [lang])
  // Muddatli to'lov yoqilgan bo'lsa — necha oyga; aks holda null (oylik narx ko'rsatilmaydi)
  const installmentMonths = paymentMethods.find(m => m.code === 'installment')?.months || null
  const monthly = price => (installmentMonths ? Number(price) / installmentMonths : null)

  useEffect(() => {
    if (tokens.access) api('/auth/me/').then(setUser).catch(() => tokens.clear())
  }, [])

  const login = async (username, password) => {
    const tk = await api("/auth/login/", { method: "POST", body: { username, password }, auth: false })
    tokens.set(tk.access, tk.refresh)
    setUser(await api('/auth/me/'))
  }
  const logout = () => { tokens.clear(); setUser(null) }

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
  const toggleFavorite = p => setFavorites(list =>
    list.some(f => f.id === p.id) ? list.filter(f => f.id !== p.id) : [favoriteFields(p), ...list])
  const clearFavorites = () => setFavorites([])

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

  // Savat belgisida turli tovarlar soni (dona emas)
  const cartCount = cart.length
  const cartTotal = cart.reduce((s, i) => s + i.qty * Number(i.price), 0)

  return (
    <StoreContext.Provider value={{
      user, login, logout, lang, changeLang, paymentMethods, installmentMonths, monthly,
      cart, cartCount, cartTotal, addToCart, setQty, removeFromCart, clearCart, refreshCart,
      favorites, isFavorite, toggleFavorite, clearFavorites, refreshFavorites,
    }}>
      {children}
    </StoreContext.Provider>
  )
}
