import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api, SHOP_NAME } from '../api'
import { LANGS, t } from '../i18n'
import { useStore } from '../store'
import { BoxIcon, CartIcon, HeartIcon, LogoutIcon, UserIcon } from './Icons'

function LangSwitch() {
  const { lang, changeLang } = useStore()
  return (
    <div className="lang-switch">
      {LANGS.map(l => (
        <button key={l.code} className={l.code === lang ? 'on' : ''} onClick={() => changeLang(l.code)}>
          {l.label}
        </button>
      ))}
    </div>
  )
}

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
          <span className="info">📍 {t('Toshkent')}</span>
          <span className="info">☎ +998 71 000 00 00</span>
          <span className="info muted">{t('Har kuni 9:00 – 21:00')}</span>
          <LangSwitch />
        </div>
      </div>

      <div className="container header-main">
        <Link to="/" className="logo">{SHOP_NAME}</Link>

        <button className="btn btn-catalog" onClick={() => setMenuOpen(o => !o)}>
          {menuOpen ? '✕' : '☰'} <span className="label">{t('Katalog')}</span>
        </button>

        <form className="search" onSubmit={search}>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder={t('Mahsulot qidirish...')} />
          <button className="btn">{t('Qidirish')}</button>
        </form>

        <nav className="header-icons">
          {user ? (
            <>
              <NavLink to="/orders" className="icon-link"><span className="ico"><BoxIcon /></span>{t('Buyurtmalar')}</NavLink>
              <button className="icon-link" onClick={logout}><span className="ico"><LogoutIcon /></span>{t('Chiqish')}</button>
            </>
          ) : (
            <NavLink to="/login" className="icon-link"><span className="ico"><UserIcon /></span>{t('Kirish')}</NavLink>
          )}
          <NavLink to="/favorites" className="icon-link">
            <span className="ico"><HeartIcon />{favorites.length > 0 && <b className="badge">{favorites.length}</b>}</span>{t('Sevimlilar')}
          </NavLink>
          <NavLink to="/cart" className="icon-link">
            <span className="ico"><CartIcon />{cartCount > 0 && <b className="badge">{cartCount}</b>}</span>{t('Savat')}
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
