import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api } from '../api'
import Logo from './Logo'
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

// Yopishqoq header balandligi --header-h ga yoziladi: yopishqoq bloklar (mundarija, profil menyusi) uning ostida qolmasin
function useHeaderHeight() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const update = () => {
      const pos = getComputedStyle(el).position
      const h = pos === 'sticky' || pos === 'fixed' ? el.offsetHeight : 0
      document.documentElement.style.setProperty('--header-h', `${h}px`)
    }
    update()
    const ro = new ResizeObserver(update)
    ro.observe(el)
    window.addEventListener('resize', update)
    return () => { ro.disconnect(); window.removeEventListener('resize', update) }
  }, [])
  return ref
}

export default function Header() {
  const headerRef = useHeaderHeight()
  const { user, logout, cartCount, favorites, storeInfo } = useStore()
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
    <header className="header" ref={headerRef}>
      <div className="topbar">
        <div className="container topbar-inner">
          {storeInfo && (
            <>
              <span className="info info-address">📍 {storeInfo.address}</span>
              <a className="info" href={`tel:${storeInfo.phone.replace(/[^\d+]/g, '')}`}>☎ {storeInfo.phone}</a>
              {storeInfo.working_hours && <span className="info muted">{storeInfo.working_hours}</span>}
            </>
          )}
          <LangSwitch />
        </div>
      </div>

      <div className="container header-main">
        <Logo />

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
              <NavLink to="/profile" className="icon-link" title={`${user.first_name} ${user.last_name}`.trim() || user.username}>
                <span className="ico"><UserIcon /></span>{t('Profil')}
              </NavLink>
              <NavLink to="/orders" className="icon-link"><span className="ico"><BoxIcon /></span>{t('Buyurtmalar')}</NavLink>
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
          {/* Chiqish — oxirida, tasodifan bosilmasligi uchun */}
          {user && (
            <button className="icon-link" onClick={logout}><span className="ico"><LogoutIcon /></span>{t('Chiqish')}</button>
          )}
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
