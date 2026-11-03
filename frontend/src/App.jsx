import { Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './pages/Home'
import Catalog from './pages/Catalog'
import ProductPage from './pages/ProductPage'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import { Login, Register } from './pages/Auth'
import Orders from './pages/Orders'
import Profile from './pages/Profile'
import Favorites from './pages/Favorites'
import { t } from './i18n'
import { useStore } from './store'

export default function App() {
  const { lang } = useStore()
  // Til o'zgarganda sahifalar qayta yuklanadi (ma'lumot yangi tilda keladi)
  return (
    <div className="app" key={lang}>
      <Header />
      <main className="container main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/catalog/:slug" element={<Catalog />} />
          <Route path="/product/:slug" element={<ProductPage />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="*" element={<div className="empty">{t('Sahifa topilmadi')}</div>} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
