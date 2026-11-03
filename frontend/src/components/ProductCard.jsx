import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { useStore } from '../store'

export function ProductImage({ src, alt, className = '' }) {
  return src
    ? <img src={src} alt={alt} className={className} loading="lazy" />
    : <div className={`img-placeholder ${className}`}>📦</div>
}

export default function ProductCard({ p }) {
  const { addToCart, cart, isFavorite, toggleFavorite } = useStore()
  const inCart = cart.some(i => i.id === p.id)

  return (
    <div className="card">
      <div className="card-badges">
        {p.discount_percent > 0 && <span className="tag tag-sale">-{p.discount_percent}%</span>}
        {p.is_hit && <span className="tag tag-hit">Xit</span>}
        {p.is_new && <span className="tag tag-new">Yangi</span>}
      </div>
      <button className={`fav ${isFavorite(p.id) ? 'on' : ''}`} onClick={() => toggleFavorite(p)}
              title="Saralanganlarga">
        {isFavorite(p.id) ? '♥' : '♡'}
      </button>
      <Link to={`/product/${p.slug}`} className="card-img">
        <ProductImage src={p.image} alt={p.name} />
      </Link>
      <Link to={`/product/${p.slug}`} className="card-name">{p.name}</Link>
      <div className="card-price">
        {p.old_price && <s className="muted">{formatPrice(p.old_price)}</s>}
        <strong>{formatPrice(p.price)}</strong>
        <span className="monthly">{formatPrice(p.monthly_price)} × 12 oy</span>
      </div>
      {p.stock > 0 ? (
        <button className={`btn ${inCart ? 'btn-outline' : ''}`} onClick={() => addToCart(p)}>
          {inCart ? 'Savatda ✓' : 'Savatga'}
        </button>
      ) : (
        <button className="btn" disabled>Tugagan</button>
      )}
    </div>
  )
}
