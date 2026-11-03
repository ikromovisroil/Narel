import { createContext, useContext, useEffect, useState } from 'react'
import { api, tokens } from './api'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokens.access))

  useEffect(() => {
    if (tokens.access) {
      api('/auth/me/')
        .then(u => (u.is_staff ? setUser(u) : tokens.clear()))
        .catch(() => tokens.clear())
        .finally(() => setLoading(false))
    }
    const onExpired = () => setUser(null)
    window.addEventListener('auth-expired', onExpired)
    return () => window.removeEventListener('auth-expired', onExpired)
  }, [])

  const login = async (username, password) => {
    const t = await api('/auth/login/', { method: 'POST', body: { username, password } })
    tokens.set(t.access, t.refresh)
    const me = await api('/auth/me/')
    if (!me.is_staff) {
      tokens.clear()
      throw { data: { detail: 'Bu hisob xodim emas. Admin panelga faqat xodimlar kira oladi.' } }
    }
    setUser(me)
  }

  const logout = () => {
    tokens.clear()
    setUser(null)
  }

  // Bo'lim ruxsati: action — "view" (ko'rish), "add" (qo'shish), "change" (tahrirlash), "delete" (o'chirish).
  // Backend ham har bir so'rovni baribir tekshiradi.
  const can = (section, action = 'view') => Boolean(user?.permissions?.[section]?.includes(action))

  // O'z ma'lumotlari (ism, ruxsatlar) o'zgarganda qayta yuklash
  const refreshMe = () => api('/auth/me/').then(setUser).catch(() => {})

  return <AuthContext.Provider value={{ user, loading, login, logout, can, refreshMe }}>{children}</AuthContext.Provider>
}

// Sahifada tugmalarni ko'rsatish/yashirish uchun
export const useCanEdit = section => useAuth().can(section, 'change')
export const usePerm = section => {
  const { can } = useAuth()
  return { view: can(section, 'view'), add: can(section, 'add'), change: can(section, 'change'), delete: can(section, 'delete') }
}
