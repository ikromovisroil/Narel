import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { t } from '../i18n'
import { HeartIcon } from './Icons'
import { useStore } from '../store'

export function ProductImage({ src, alt, className = '' }) {
  return src
    ? <img src={src} alt={alt} className={className} loading="lazy" />
    : <div className={`img-placeholder ${className}`}>📦</div>
}

export default function ProductCard({ p }) {
  const { addToCart, cart, isFavorite, toggleFavorite, installmentMonths, monthly } = useStore()
  const inCart = cart.some(i => i.id === p.id)

  return (
    <div className="card">
      <div className="card-badges">
        {p.discount_percent > 0 && <span className="tag tag-sale">-{p.discount_percent}%</span>}
        {p.is_hit && <span className="tag tag-hit">{t('Xit')}</span>}
        {p.is_new && <span className="tag tag-new">{t('Yangi')}</span>}
      </div>
      <button className={`fav ${isFavorite(p.id) ? 'on' : ''}`} onClick={() => toggleFavorite(p)}
              title={isFavorite(p.id) ? t('Sevimlilardan olib tashlash') : t("Sevimlilarga qo'shish")}
              aria-pressed={isFavorite(p.id)}>
        <HeartIcon size={20} filled={isFavorite(p.id)} />
      </button>
      <Link to={`/product/${p.slug}`} className="card-img">
        <ProductImage src={p.image} alt={p.name} />
      </Link>
      <Link to={`/product/${p.slug}`} className="card-name">{p.name}</Link>
      <div className="card-price">
        {p.old_price && <s className="muted">{formatPrice(p.old_price)}</s>}
        <strong>{formatPrice(p.price)}</strong>
        {installmentMonths && (
          <span className="monthly">{t('{sum} × {n} oy', { sum: formatPrice(monthly(p.price)), n: installmentMonths })}</span>
        )}
      </div>
      {p.stock > 0 ? (
        <button className={`btn ${inCart ? 'btn-outline' : ''}`} onClick={() => addToCart(p)}>
          {inCart ? t('Savatda ✓') : t('Savatga')}
        </button>
      ) : (
        <button className="btn" disabled>{t('Tugagan')}</button>
      )}
    </div>
  )
}
