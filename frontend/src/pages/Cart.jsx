import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../api'
import ConfirmButton from '../components/ConfirmButton'
import { HeartIcon, TrashIcon } from '../components/Icons'
import { ProductImage } from '../components/ProductCard'
import { t } from '../i18n'
import { useStore } from '../store'

export default function Cart() {
  const {
    cart, cartTotal, cartCount, setQty, removeFromCart, clearCart, refreshCart, isFavorite, toggleFavorite, storeInfo,
  } = useStore()
  const navigate = useNavigate()

  // Ombordagi son va narx eskirgan bo'lishi mumkin — sahifa ochilganda yangilaymiz
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (cart.length) refreshCart() }, [])

  if (!cart.length) {
    return (
      <div className="empty">
        <div style={{ fontSize: 48 }}>🛒</div>
        <h2>{t("Savatingiz bo'sh")}</h2>
        <Link className="btn" to="/catalog">{t('Xaridni boshlash')}</Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">{t('Savat')} <span className="muted">({cartCount})</span></h1>
      <div className="cart">
        <div className="cart-items">
          {cart.map(i => (
            <div key={i.id} className="cart-row">
              <Link to={`/product/${i.slug}`} className="cart-img"><ProductImage src={i.image} alt={i.name} /></Link>
              <div className="cart-name">
                <Link to={`/product/${i.slug}`}>{i.name}</Link>
                <span className={`cart-stock ${i.stock > 0 ? 'muted' : 'danger-text'}`}>
                  {i.stock > 0 ? t('Omborda: {n} dona', { n: i.stock }) : t('Tugagan')}
                </span>
              </div>
              {/* Kompyuterda qty va summa alohida ustunlar, telefonda nom ostida bitta qator */}
              <div className="cart-bottom">
                <div className="qty">
                  <button onClick={() => setQty(i.id, i.qty - 1)} disabled={i.qty <= 1} aria-label="−">−</button>
                  <span>{i.qty}</span>
                  <button onClick={() => setQty(i.id, i.qty + 1)} disabled={i.qty >= i.stock} aria-label="+">+</button>
                </div>
                <strong className="cart-sum">{formatPrice(i.qty * i.price)}</strong>
              </div>
              <div className="cart-actions">
                <button className={`icon-btn ${isFavorite(i.id) ? 'on' : ''}`} onClick={() => toggleFavorite(i)}
                        title={isFavorite(i.id) ? t('Sevimlilardan olib tashlash') : t("Sevimlilarga qo'shish")}
                        aria-pressed={isFavorite(i.id)}>
                  <HeartIcon size={20} filled={isFavorite(i.id)} />
                </button>
                <button className="icon-btn danger-hover" onClick={() => removeFromCart(i.id)} title={t("O'chirish")}>
                  <TrashIcon size={20} />
                </button>
              </div>
            </div>
          ))}
          <div className="list-footer">
            <ConfirmButton className="clear-btn" title={t('Savatni tozalaysizmi?')}
                           text={t("Savatdagi barcha mahsulotlar olib tashlanadi.")} okLabel={t('Tozalash')}
                           onConfirm={clearCart}>
              <TrashIcon size={16} /> {t('Savatni tozalash')}
            </ConfirmButton>
          </div>
        </div>
        <div className="buy-box">
          <div className="row-between"><span>{t('Mahsulotlar ({n})', { n: cartCount })}</span><span>{formatPrice(cartTotal)}</span></div>
          {storeInfo?.delivery_enabled ? (
            <div className="row-between">
              <span>{t('Yetkazib berish')}</span>
              {Number(storeInfo.delivery_price)
                ? <span>{formatPrice(storeInfo.delivery_price)}</span>
                : <span className="ok">{t('Bepul')}</span>}
            </div>
          ) : storeInfo && (
            <div className="row-between"><span>{t("Do'kondan olib ketish")}</span><span className="ok">{t('Bepul')}</span></div>
          )}
          <hr />
          <div className="row-between big"><span>{t('Jami')}</span><strong>{formatPrice(cartTotal)}</strong></div>
          <button className="btn btn-lg" onClick={() => navigate('/checkout')}>{t('Rasmiylashtirish')}</button>
        </div>
      </div>
    </div>
  )
}
