import { Button, Result, Spin } from 'antd'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './auth'
import AdminLayout from './AdminLayout'
import { MENU } from './menu'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import Products from './pages/Products'
import ProductForm from './pages/ProductForm'
import Categories from './pages/Categories'
import Brands from './pages/Brands'
import Banners from './pages/Banners'
import Customers from './pages/Customers'
import Settings from './pages/Settings'
import Staff from './pages/Staff'
import Comments from './pages/Comments'

// Ruxsatsiz bo'lim ochilsa — tushunarli xabar
function Guard({ section, children }) {
  const { can } = useAuth()
  const navigate = useNavigate()
  if (can(section)) return children
  return (
    <Result
      status="403" title="Ruxsat yo'q"
      subTitle="Bu bo'limni ko'rish uchun ruxsatingiz yo'q. Kerak bo'lsa administratorga murojaat qiling."
      extra={<Button type="primary" onClick={() => navigate('/')}>Bosh sahifaga</Button>}
    />
  )
}

// Bosh sahifaga ruxsat bo'lmasa — birinchi ruxsat berilgan bo'limga o'tkazamiz
function Home() {
  const { can } = useAuth()
  if (can('dashboard')) return <Dashboard />
  const first = MENU.find(m => can(m.section))
  return first ? <Navigate to={first.key} replace /> : (
    <Result status="403" title="Ruxsatlar berilmagan"
            subTitle="Sizga hali birorta bo'lim uchun ruxsat berilmagan. Administratorga murojaat qiling." />
  )
}

export default function App() {
  const { user, loading } = useAuth()

  if (loading) return <div style={{ display: 'grid', placeItems: 'center', height: '100vh' }}><Spin size="large" /></div>
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/orders" element={<Guard section="orders"><Orders /></Guard>} />
        <Route path="/products" element={<Guard section="products"><Products /></Guard>} />
        <Route path="/products/new" element={<Guard section="products"><ProductForm /></Guard>} />
        <Route path="/products/:id" element={<Guard section="products"><ProductForm /></Guard>} />
        <Route path="/categories" element={<Guard section="categories"><Categories /></Guard>} />
        <Route path="/brands" element={<Guard section="brands"><Brands /></Guard>} />
        <Route path="/banners" element={<Guard section="banners"><Banners /></Guard>} />
        <Route path="/customers" element={<Guard section="customers"><Customers /></Guard>} />
        <Route path="/comments" element={<Guard section="comments"><Comments /></Guard>} />
        <Route path="/staff" element={<Guard section="staff"><Staff /></Guard>} />
        <Route path="/settings" element={<Guard section="settings"><Settings /></Guard>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
