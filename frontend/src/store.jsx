import { createContext, useContext, useEffect, useState } from 'react'
import { api, tokens } from './api'

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

  useEffect(() => {
    if (tokens.access) api('/auth/me/').then(setUser).catch(() => tokens.clear())
  }, [])

  const login = async (username, password) => {
    const t = await api('/auth/login/', { method: 'POST', body: { username, password }, auth: false })
    tokens.set(t.access, t.refresh)
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
  const clearCart = () => setCart([])

  const isFavorite = id => favorites.some(f => f.id === id)
  const toggleFavorite = p => setFavorites(list =>
    list.some(f => f.id === p.id) ? list.filter(f => f.id !== p.id) : [...list, p])

  const cartCount = cart.reduce((s, i) => s + i.qty, 0)
  const cartTotal = cart.reduce((s, i) => s + i.qty * Number(i.price), 0)

  return (
    <StoreContext.Provider value={{
      user, login, logout,
      cart, cartCount, cartTotal, addToCart, setQty, removeFromCart, clearCart,
      favorites, isFavorite, toggleFavorite,
    }}>
      {children}
    </StoreContext.Provider>
  )
}
