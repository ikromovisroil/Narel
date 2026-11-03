import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, formatPrice } from '../api'
import { useStore } from '../store'

const PAYMENT = { cash: 'Naqd pul', card: 'Karta', installment: 'Muddatli to\'lov' }

export default function Orders() {
  const { user } = useStore()
  const [orders, setOrders] = useState(null)

  useEffect(() => {
    if (user) api('/orders/').then(r => setOrders(r.results)).catch(() => setOrders([]))
  }, [user])

  if (!user) {
    return (
      <div className="empty">
        <h2>Buyurtmalarni ko'rish uchun tizimga kiring</h2>
        <Link className="btn" to="/login?next=/orders">Kirish</Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Buyurtmalarim</h1>
      {!orders ? <div className="muted">Yuklanmoqda...</div>
        : !orders.length ? <div className="empty">Hali buyurtma yo'q. <Link to="/catalog">Katalogga o'tish</Link></div>
        : orders.map(o => (
          <div key={o.id} className="order">
            <div className="order-head">
              <b>Buyurtma #{o.id}</b>
              <span className="muted">{new Date(o.created_at).toLocaleString('uz-UZ')}</span>
              <span className={`status status-${o.status}`}>{o.status_display}</span>
            </div>
            {o.items.map(i => (
              <div key={i.product} className="row-between small">
                <Link to={`/product/${i.product_slug}`}>{i.product_name} × {i.quantity}</Link>
                <span>{formatPrice(i.subtotal)}</span>
              </div>
            ))}
            <div className="row-between">
              <span className="muted small">To'lov: {PAYMENT[o.payment_method]}</span>
              <strong>{formatPrice(o.total)}</strong>
            </div>
          </div>
        ))}
    </div>
  )
}
