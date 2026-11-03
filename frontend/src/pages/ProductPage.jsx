import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, formatPrice } from '../api'
import Comments from '../components/Comments'
import { HeartIcon } from '../components/Icons'
import { ProductImage } from '../components/ProductCard'
import { t } from '../i18n'
import { useStore } from '../store'

export default function ProductPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { addToCart, cart, isFavorite, toggleFavorite, installmentMonths, monthly } = useStore()
  const [p, setP] = useState(null)
  const [error, setError] = useState(false)
  const [img, setImg] = useState(null)
  const [tab, setTab] = useState('specs')
  const [commentSummary, setCommentSummary] = useState(null)

  useEffect(() => {
    setP(null); setError(false)
    api(`/products/${slug}/`, { auth: false })
      .then(d => { setP(d); setImg(d.image || d.images[0]?.image || null) })
      .catch(() => setError(true))
  }, [slug])

  if (error) return <div className="empty">{t('Mahsulot topilmadi')}</div>
  if (!p) return <div className="muted">{t('Yuklanmoqda...')}</div>

  const gallery = [p.image, ...p.images.map(i => i.image)].filter(Boolean)
  const inCart = cart.some(i => i.id === p.id)

  return (
    <div>
      <div className="crumbs">
        <Link to="/">{t('Bosh sahifa')}</Link> ›{' '}
        <Link to={`/catalog/${p.category.slug}`}>{p.category.name}</Link> › {p.name}
      </div>
      <h1 className="page-title">{p.name}</h1>
      <div className="muted small">
        {t('Mahsulot kodi')}: {p.sku || '—'}{' '}
        {p.brand && <>· {t('Brend')}: <Link to={`/catalog?brand=${p.brand.slug}`}>{p.brand.name}</Link></>}
      </div>

      <div className="product">
        <div className="gallery">
          <div className="gallery-main"><ProductImage src={img} alt={p.name} /></div>
          {gallery.length > 1 && (
            <div className="thumbs">
              {gallery.map(src => (
                <button key={src} className={src === img ? 'on' : ''} onClick={() => setImg(src)}>
                  <img src={src} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="product-info">
          <h3>{t('Asosiy xususiyatlar')}</h3>
          <dl className="specs short">
            {p.specs.slice(0, 5).map(s => <div key={s.name}><dt>{s.name}</dt><dd>{s.value}</dd></div>)}
          </dl>
          <button className="link" onClick={() => setTab('specs')}>{t('Barcha xususiyatlar ↓')}</button>
        </div>

        <div className="buy-box">
          {p.discount_percent > 0 && (
            <div className="old-price"><s>{formatPrice(p.old_price)}</s> <span className="tag tag-sale">-{p.discount_percent}%</span></div>
          )}
          <div className="big-price">{formatPrice(p.price)}</div>
          {installmentMonths && (
            <div className="installment">
              <b>{t('{sum} dan × {n} oy', { sum: formatPrice(monthly(p.price)), n: installmentMonths })}</b>
              <div className="muted small">{t("Muddatli to'lov")}</div>
            </div>
          )}
          <div className={p.stock > 0 ? 'stock ok' : 'stock no'}>
            {p.stock > 0 ? `✓ ${t('Mavjud: {n} dona', { n: p.stock })}` : t('Tugagan')}
          </div>
          <button className="btn btn-lg" disabled={!p.stock}
                  onClick={() => (inCart ? navigate('/cart') : addToCart(p))}>
            {inCart ? t("Savatga o'tish") : t("Savatga qo'shish")}
          </button>
          <button className="btn btn-lg btn-outline" disabled={!p.stock}
                  onClick={() => { if (!inCart) addToCart(p); navigate('/checkout') }}>
            {t('Bir klikda sotib olish')}
          </button>
          <button className={`fav-line ${isFavorite(p.id) ? 'on' : ''}`} onClick={() => toggleFavorite(p)}
                  aria-pressed={isFavorite(p.id)}>
            <HeartIcon size={18} filled={isFavorite(p.id)} />
            {isFavorite(p.id) ? t('Sevimlilarda') : t("Sevimlilarga qo'shish")}
          </button>
          <ul className="perks-list muted small">
            <li>🚚 {t("Toshkent bo'ylab bepul yetkazish")}</li>
            <li>🛡 {t('Rasmiy kafolat')}</li>
          </ul>
        </div>
      </div>

      <div className="tabs">
        <button className={tab === 'specs' ? 'on' : ''} onClick={() => setTab('specs')}>{t('Xususiyatlar')}</button>
        <button className={tab === 'desc' ? 'on' : ''} onClick={() => setTab('desc')}>{t('Tavsif')}</button>
        <button className={tab === 'comments' ? 'on' : ''} onClick={() => setTab('comments')}>
          {t('Izohlar')}
          {commentSummary?.count > 0 && <span className="tab-count">{commentSummary.count}</span>}
          {commentSummary?.rating && <span className="tab-rating">★ {commentSummary.rating}</span>}
        </button>
      </div>
      <div className={`tab-body ${tab === 'comments' ? 'wide' : ''}`}>
        {tab === 'specs' && (
          <dl className="specs">
            {p.specs.map(s => <div key={s.name}><dt>{s.name}</dt><dd>{s.value}</dd></div>)}
          </dl>
        )}
        {tab === 'desc' && <p className="description">{p.description || t('Tavsif mavjud emas.')}</p>}
        {/* Doim yuklanadi — tab sarlavhasida izohlar soni va baho ko'rinsin */}
        <div style={{ display: tab === 'comments' ? 'block' : 'none' }}>
          <Comments slug={p.slug} onSummary={setCommentSummary} />
        </div>
      </div>
    </div>
  )
}
