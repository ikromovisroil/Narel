import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../api'
import { ProductImage } from '../components/ProductCard'
import { useStore } from '../store'

export default function Cart() {
  const { cart, cartTotal, cartCount, setQty, removeFromCart, clearCart } = useStore()
  const navigate = useNavigate()

  if (!cart.length) {
    return (
      <div className="empty">
        <div style={{ fontSize: 48 }}>🛒</div>
        <h2>Savatingiz bo'sh</h2>
        <Link className="btn" to="/catalog">Xaridni boshlash</Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Savat <span className="muted">({cartCount})</span></h1>
      <div className="cart">
        <div className="cart-items">
          {cart.map(i => (
            <div key={i.id} className="cart-row">
              <Link to={`/product/${i.slug}`} className="cart-img"><ProductImage src={i.image} alt={i.name} /></Link>
              <div className="cart-name">
                <Link to={`/product/${i.slug}`}>{i.name}</Link>
                <button className="link danger" onClick={() => removeFromCart(i.id)}>O'chirish</button>
              </div>
              <div className="qty">
                <button onClick={() => setQty(i.id, i.qty - 1)} disabled={i.qty <= 1}>−</button>
                <span>{i.qty}</span>
                <button onClick={() => setQty(i.id, i.qty + 1)} disabled={i.qty >= i.stock}>+</button>
              </div>
              <strong className="cart-sum">{formatPrice(i.qty * i.price)}</strong>
            </div>
          ))}
          <button className="link danger" onClick={clearCart}>Savatni tozalash</button>
        </div>
        <div className="buy-box">
          <div className="row-between"><span>Mahsulotlar ({cartCount})</span><span>{formatPrice(cartTotal)}</span></div>
          <div className="row-between"><span>Yetkazib berish</span><span className="ok">Bepul</span></div>
          <hr />
          <div className="row-between big"><span>Jami</span><strong>{formatPrice(cartTotal)}</strong></div>
          <button className="btn btn-lg" onClick={() => navigate('/checkout')}>Rasmiylashtirish</button>
        </div>
      </div>
    </div>
  )
}
