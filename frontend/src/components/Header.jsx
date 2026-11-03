import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api, SHOP_NAME } from '../api'
import { useStore } from '../store'

export default function Header() {
  const { user, logout, cartCount, favorites } = useStore()
  const [categories, setCategories] = useState([])
  const [menuOpen, setMenuOpen] = useState(false)
  const [active, setActive] = useState(null)
  const [q, setQ] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api('/categories/', { auth: false }).then(c => { setCategories(c); setActive(c[0]?.id) }).catch(() => {})
  }, [])

  const search = e => {
    e.preventDefault()
    navigate(`/catalog?search=${encodeURIComponent(q.trim())}`)
  }
  const go = path => { setMenuOpen(false); navigate(path) }
  const activeCat = categories.find(c => c.id === active)

  return (
    <header className="header">
      <div className="topbar">
        <div className="container topbar-inner">
          <span>📍 Toshkent</span>
          <span>☎ +998 71 000 00 00</span>
          <span className="muted">Har kuni 9:00 – 21:00</span>
        </div>
      </div>

      <div className="container header-main">
        <Link to="/" className="logo">{SHOP_NAME}</Link>

        <button className="btn btn-catalog" onClick={() => setMenuOpen(o => !o)}>
          {menuOpen ? '✕' : '☰'} Katalog
        </button>

        <form className="search" onSubmit={search}>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Mahsulot qidirish..." />
          <button className="btn">Qidirish</button>
        </form>

        <nav className="header-icons">
          {user ? (
            <>
              <NavLink to="/orders" className="icon-link"><span>📦</span>Buyurtmalar</NavLink>
              <button className="icon-link" onClick={logout}><span>👤</span>Chiqish</button>
            </>
          ) : (
            <NavLink to="/login" className="icon-link"><span>👤</span>Kirish</NavLink>
          )}
          <NavLink to="/favorites" className="icon-link">
            <span>♡{favorites.length > 0 && <b className="badge">{favorites.length}</b>}</span>Saralangan
          </NavLink>
          <NavLink to="/cart" className="icon-link">
            <span>🛒{cartCount > 0 && <b className="badge">{cartCount}</b>}</span>Savat
          </NavLink>
        </nav>
      </div>

      <div className="container cat-strip">
        {categories.map(c => <Link key={c.id} to={`/catalog/${c.slug}`}>{c.name}</Link>)}
      </div>

      {menuOpen && (
        <div className="mega" onClick={() => setMenuOpen(false)}>
          <div className="container mega-inner" onClick={e => e.stopPropagation()}>
            <ul className="mega-left">
              {categories.map(c => (
                <li key={c.id} className={c.id === active ? 'active' : ''}
                    onMouseEnter={() => setActive(c.id)} onClick={() => go(`/catalog/${c.slug}`)}>
                  {c.name} <span>›</span>
                </li>
              ))}
            </ul>
            {activeCat && (
              <div className="mega-right">
                <h3 onClick={() => go(`/catalog/${activeCat.slug}`)}>{activeCat.name}</h3>
                <div className="mega-grid">
                  {activeCat.children.map(ch => (
                    <a key={ch.id} onClick={() => go(`/catalog/${ch.slug}`)}>{ch.name}</a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
