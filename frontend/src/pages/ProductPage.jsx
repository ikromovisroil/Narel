import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, formatPrice } from '../api'
import { ProductImage } from '../components/ProductCard'
import { useStore } from '../store'

export default function ProductPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { addToCart, cart, isFavorite, toggleFavorite } = useStore()
  const [p, setP] = useState(null)
  const [error, setError] = useState(false)
  const [img, setImg] = useState(null)
  const [tab, setTab] = useState('specs')

  useEffect(() => {
    setP(null); setError(false)
    api(`/products/${slug}/`, { auth: false })
      .then(d => { setP(d); setImg(d.image || d.images[0]?.image || null) })
      .catch(() => setError(true))
  }, [slug])

  if (error) return <div className="empty">Mahsulot topilmadi</div>
  if (!p) return <div className="muted">Yuklanmoqda...</div>

  const gallery = [p.image, ...p.images.map(i => i.image)].filter(Boolean)
  const inCart = cart.some(i => i.id === p.id)

  return (
    <div>
      <div className="crumbs">
        <Link to="/">Bosh sahifa</Link> ›{' '}
        <Link to={`/catalog/${p.category.slug}`}>{p.category.name}</Link> › {p.name}
      </div>
      <h1 className="page-title">{p.name}</h1>
      <div className="muted small">Artikul: {p.sku || '—'} {p.brand && <>· Brend: <Link to={`/catalog?brand=${p.brand.slug}`}>{p.brand.name}</Link></>}</div>

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
          <h3>Asosiy xususiyatlar</h3>
          <dl className="specs short">
            {p.specs.slice(0, 5).map(s => <div key={s.name}><dt>{s.name}</dt><dd>{s.value}</dd></div>)}
          </dl>
          <button className="link" onClick={() => setTab('specs')}>Barcha xususiyatlar ↓</button>
        </div>

        <div className="buy-box">
          {p.discount_percent > 0 && (
            <div className="old-price"><s>{formatPrice(p.old_price)}</s> <span className="tag tag-sale">-{p.discount_percent}%</span></div>
          )}
          <div className="big-price">{formatPrice(p.price)}</div>
          <div className="installment">
            <b>{formatPrice(p.monthly_price)}</b> dan × 12 oy
            <div className="muted small">Muddatli to'lov</div>
          </div>
          <div className={p.stock > 0 ? 'stock ok' : 'stock no'}>
            {p.stock > 0 ? `✓ Mavjud: ${p.stock} dona` : 'Tugagan'}
          </div>
          <button className="btn btn-lg" disabled={!p.stock}
                  onClick={() => (inCart ? navigate('/cart') : addToCart(p))}>
            {inCart ? 'Savatga o\'tish' : 'Savatga qo\'shish'}
          </button>
          <button className="btn btn-lg btn-outline" disabled={!p.stock}
                  onClick={() => { if (!inCart) addToCart(p); navigate('/checkout') }}>
            Bir klikda sotib olish
          </button>
          <button className="link" onClick={() => toggleFavorite(p)}>
            {isFavorite(p.id) ? '♥ Saralanganlarda' : '♡ Saralanganlarga qo\'shish'}
          </button>
          <ul className="perks-list muted small">
            <li>🚚 Toshkent bo'ylab bepul yetkazish</li>
            <li>🛡 Rasmiy kafolat</li>
          </ul>
        </div>
      </div>

      <div className="tabs">
        <button className={tab === 'specs' ? 'on' : ''} onClick={() => setTab('specs')}>Xususiyatlar</button>
        <button className={tab === 'desc' ? 'on' : ''} onClick={() => setTab('desc')}>Tavsif</button>
      </div>
      <div className="tab-body">
        {tab === 'specs' ? (
          <dl className="specs">
            {p.specs.map(s => <div key={s.name}><dt>{s.name}</dt><dd>{s.value}</dd></div>)}
          </dl>
        ) : (
          <p className="description">{p.description || 'Tavsif mavjud emas.'}</p>
        )}
      </div>
    </div>
  )
}
