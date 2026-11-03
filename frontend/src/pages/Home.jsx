import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import ProductCard from '../components/ProductCard'
import { pickupWhere } from '../components/StoreInfo'
import { t } from '../i18n'
import { useStore } from '../store'

function BannerSlider({ banners }) {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (banners.length < 2) return
    const t = setInterval(() => setI(x => (x + 1) % banners.length), 5000)
    return () => clearInterval(t)
  }, [banners.length])
  if (!banners.length) return null
  const b = banners[i]
  return (
    <div className="slider" style={b.image ? { backgroundImage: `url(${b.image})` } : undefined}>
      <div className={`slide slide-${i % 3}`}>
        <h2>{b.title}</h2>
        {b.subtitle && <p>{b.subtitle}</p>}
        <Link className="btn btn-light" to={b.link || '/catalog'}>{t('Batafsil')}</Link>
      </div>
      <div className="dots">
        {banners.map((_, k) => <button key={k} className={k === i ? 'on' : ''} onClick={() => setI(k)} />)}
      </div>
    </div>
  )
}

function Section({ title, query, more }) {
  const [items, setItems] = useState(null)
  useEffect(() => {
    api(`/products/?${query}`, { auth: false }).then(r => setItems(r.results)).catch(() => setItems([]))
  }, [query])
  if (items && !items.length) return null
  return (
    <section className="section">
      <div className="section-head">
        <h2>{title}</h2>
        <Link to={more}>{t('Barchasi ›')}</Link>
      </div>
      <div className="grid grid-scroll">
        {items ? items.slice(0, 10).map(p => <ProductCard key={p.id} p={p} />)
               : <div className="muted">{t('Yuklanmoqda...')}</div>}
      </div>
    </section>
  )
}

export default function Home() {
  const { installmentMonths, storeInfo } = useStore()
  const freeDelivery = storeInfo && !Number(storeInfo.delivery_price)
  const [banners, setBanners] = useState([])
  const [categories, setCategories] = useState([])
  const [brands, setBrands] = useState([])

  useEffect(() => {
    api('/banners/', { auth: false }).then(setBanners).catch(() => {})
    api('/categories/', { auth: false }).then(setCategories).catch(() => {})
    api('/brands/', { auth: false }).then(setBrands).catch(() => {})
  }, [])

  return (
    <>
      <BannerSlider banners={banners} />

      <div className="perks">
        {storeInfo?.delivery_enabled ? (
          <div><b>🚚 {freeDelivery ? t('Bepul yetkazish') : t('Yetkazib berish')}</b><span>{storeInfo.delivery_note}</span></div>
        ) : storeInfo?.pickup_enabled && (
          <div><b>🏬 {t("Do'kondan olib ketish")}</b><span>{pickupWhere(storeInfo)}</span></div>
        )}
        {installmentMonths && (
          <div><b>💳 {t("Muddatli to'lov")}</b><span>{t("{n} oygacha bo'lib to'lash", { n: installmentMonths })}</span></div>
        )}
        <div><b>🛡 {t('Rasmiy kafolat')}</b><span>{t('Barcha mahsulotlarga')}</span></div>
        <div><b>↩ {t('Qaytarish')}</b><span>{t('10 kun ichida')}</span></div>
      </div>

      <section className="section">
        <div className="section-head"><h2>{t('Ommabop kategoriyalar')}</h2></div>
        <div className="cat-tiles">
          {categories.flatMap(c => c.children).slice(0, 12).map(c => (
            <Link key={c.id} to={`/catalog/${c.slug}`} className="cat-tile">
              {c.icon ? <img src={c.icon} alt="" /> : <span className="cat-ico">{c.name[0]}</span>}
              {c.name}
            </Link>
          ))}
        </div>
      </section>

      <Section title={`🔥 ${t('Xit savdo')}`} query="is_hit=true" more="/catalog?is_hit=true" />
      <Section title={`💰 ${t('Chegirmalar')}`} query="discount=true" more="/catalog?discount=true" />
      <Section title={`✨ ${t('Yangi mahsulotlar')}`} query="is_new=true" more="/catalog?is_new=true" />

      {brands.length > 0 && (
        <section className="section">
          <div className="section-head"><h2>{t('Brendlar')}</h2></div>
          <div className="brands">
            {brands.map(b => (
              <Link key={b.id} to={`/catalog?brand=${b.slug}`} className="brand">
                {b.logo ? <img src={b.logo} alt={b.name} /> : b.name}
              </Link>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
