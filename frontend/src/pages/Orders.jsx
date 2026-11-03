import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, formatPrice } from '../api'
import { dateLocale, t } from '../i18n'
import { useStore } from '../store'

// Sozlamalarda o'chirilgan usullar uchun zaxira nomlar
const PAYMENT = {
  cash: 'Naqd pul', card: 'Karta', installment: "Muddatli to'lov",
  click: 'Click', payme: 'Payme', paynet: 'Paynet', uzum: 'Uzum Bank',
}
const STATUS = {
  new: 'Yangi buyurtma', confirmed: 'Tasdiqlangan', shipped: 'Yuborilgan',
  delivered: 'Yetkazilgan', cancelled: 'Bekor qilingan',
}

export default function Orders() {
  const { user, paymentMethods } = useStore()
  const paymentTitle = code => paymentMethods.find(m => m.code === code)?.title || t(PAYMENT[code] || code)
  const [orders, setOrders] = useState(null)

  useEffect(() => {
    if (user) api('/orders/').then(r => setOrders(r.results)).catch(() => setOrders([]))
  }, [user])

  if (!user) {
    return (
      <div className="empty">
        <h2>{t("Buyurtmalarni ko'rish uchun tizimga kiring")}</h2>
        <Link className="btn" to="/login?next=/orders">{t('Kirish')}</Link>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">{t('Buyurtmalarim')}</h1>
      {!orders ? <div className="muted">{t('Yuklanmoqda...')}</div>
        : !orders.length ? (
          <div className="empty">{t("Hali buyurtma yo'q.")} <Link to="/catalog">{t("Katalogga o'tish")}</Link></div>
        ) : orders.map(o => (
          <div key={o.id} className="order">
            <div className="order-head">
              <b>{t('Buyurtma #{id}', { id: o.id })}</b>
              <span className="muted">{new Date(o.created_at).toLocaleString(dateLocale())}</span>
              <span className={`status status-${o.status}`}>{t(STATUS[o.status])}</span>
            </div>
            {o.items.map(i => (
              <div key={i.product} className="row-between small">
                <Link to={`/product/${i.product_slug}`}>{i.product_name} × {i.quantity}</Link>
                <span>{formatPrice(i.subtotal)}</span>
              </div>
            ))}
            <div className="row-between">
              <span className="muted small">{t("To'lov: {p}", { p: paymentTitle(o.payment_method) })}</span>
              <strong>{formatPrice(o.total)}</strong>
            </div>
          </div>
        ))}
    </div>
  )
}
