import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, formatPrice } from '../api'
import StoreInfo from '../components/StoreInfo'
import { dateLocale, t } from '../i18n'
import { useStore } from '../store'

// Sozlamalarda o'chirilgan usullar uchun zaxira nomlar
const PAYMENT = {
  cash: 'Naqd pul', card: 'Karta', installment: "Muddatli to'lov",
  click: 'Click', payme: 'Payme', paynet: 'Paynet', uzum: 'Uzum Bank',
}

// Bosqichlar: kuryer va olib ketish uchun alohida nomlar
const STEPS = {
  courier: [
    ['new', 'Qabul qilindi'], ['confirmed', 'Tasdiqlandi'], ['shipped', "Yo'lda"], ['delivered', 'Yetkazildi'],
  ],
  pickup: [
    ['new', 'Qabul qilindi'], ['confirmed', 'Tayyorlanmoqda'], ['shipped', 'Olib ketishga tayyor'], ['delivered', 'Topshirildi'],
  ],
}
const ORDER = ['new', 'confirmed', 'shipped', 'delivered']
const fmtDate = d => new Date(d).toLocaleDateString('ru-RU')

function Timeline({ order }) {
  if (order.status === 'cancelled') return <div className="order-cancelled">✕ {t('Buyurtma bekor qilingan')}</div>
  // Yetkazilgan bo'lsa — barcha bosqichlar bajarilgan (✓)
  const current = order.status === 'delivered' ? ORDER.length : ORDER.indexOf(order.status)
  const steps = STEPS[order.delivery_method] || STEPS.courier
  return (
    <ol className="timeline">
      {steps.map(([code, label], i) => (
        <li key={code} className={i < current ? 'done' : i === current ? 'current' : ''}>
          <span className="dot">{i < current ? '✓' : i + 1}</span>
          <span className="label">{t(label)}</span>
        </li>
      ))}
    </ol>
  )
}

function DeliveryLine({ order }) {
  if (order.status === 'cancelled') return null
  if (order.delivery_method === 'pickup') {
    return order.status === 'delivered' ? null : <StoreInfo title={t('Olib ketish joyi')} info={order.pickup_branch_info} />
  }
  if (order.status === 'delivered') return <div className="expected done">✓ {t('Buyurtma yetkazildi')}</div>
  if (!order.expected_date) return <div className="expected muted">{t("Yetkazish sanasi tez orada aniqlanadi")}</div>

  const days = Math.round((new Date(order.expected_date) - new Date(new Date().toDateString())) / 86400000)
  const when = days === 0 ? t('bugun') : days === 1 ? t('ertaga') : fmtDate(order.expected_date)

  // Kechikish: sana va'dadan keyinga surilgan yoki o'tib ketgan — mijozdan uzr so'raymiz
  if (order.is_delayed) {
    return (
      <div className="delay-box">
        <b>😔 {t("Uzr so'raymiz! Buyurtmangiz biroz kechikmoqda.")}</b>
        {days >= 0 ? (
          <span>🚚 {t('Yangi taxminiy sana: {date}', { date: when })}
            {order.original_expected_date && <span className="muted"> ({t('avval: {date}', { date: fmtDate(order.original_expected_date) })})</span>}
          </span>
        ) : (
          <span>{t("Operatorimiz tez orada siz bilan bog'lanib, yangi sanani aytadi.")}</span>
        )}
        {order.delay_note && <span className="muted">{t('Sabab: {note}', { note: order.delay_note })}</span>}
      </div>
    )
  }

  return (
    <div className="expected">
      🚚 {t('Taxminiy yetkazish: {date}', { date: when })}
      {order.status === 'new' && <span className="muted small"> · {t('buyurtma tasdiqlangach aniqlashtiriladi')}</span>}
    </div>
  )
}

export default function Orders() {
  const { user, paymentMethods } = useStore()
  const paymentTitle = code => paymentMethods.find(m => m.code === code)?.title || t(PAYMENT[code] || code)
  const [orders, setOrders] = useState(null)
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  // Oxirgi 5 ta buyurtma; "Ko'proq ko'rish" har bosilganda yana 5 tasi qo'shiladi
  const load = async (n, append) => {
    const r = await api(`/orders/?page=${n}`)
    setOrders(prev => (append ? [...(prev || []), ...r.results] : r.results))
    setCount(r.count)
    setPage(n)
    setHasMore(!!r.next)
  }

  useEffect(() => {
    if (user) load(1, false).catch(() => setOrders([]))
  }, [user])

  const more = async () => {
    setLoadingMore(true)
    try { await load(page + 1, true) } catch { /* tarmoq xatosi — tugma qoladi */ } finally { setLoadingMore(false) }
  }

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
      <h1 className="page-title">
        {t('Buyurtmalarim')}
        {count > 0 && <span className="muted title-count">{t('{n} ta', { n: count })}</span>}
      </h1>
      {!orders ? <div className="muted">{t('Yuklanmoqda...')}</div>
        : !orders.length ? (
          <div className="empty">{t("Hali buyurtma yo'q.")} <Link to="/catalog">{t("Katalogga o'tish")}</Link></div>
        ) : orders.map(o => (
          <div key={o.id} className="order">
            <div className="order-head">
              <b>{t('Buyurtma #{id}', { id: o.id })}</b>
              <span className="muted">{new Date(o.created_at).toLocaleString(dateLocale())}</span>
              <span className="muted small">
                {o.delivery_method === 'pickup' ? t("Do'kondan olib ketish") : t('Kuryer orqali')}
              </span>
            </div>

            <Timeline order={o} />
            <DeliveryLine order={o} />

            <div className="order-items">
              {o.items.map(i => (
                <div key={i.product} className="row-between small">
                  {i.product_slug
                    ? <Link to={`/product/${i.product_slug}`}>{i.product_name} × {i.quantity}</Link>
                    : <span>{i.product_name} × {i.quantity}</span>}
                  <span>{formatPrice(i.subtotal)}</span>
                </div>
              ))}
              {Number(o.delivery_price) > 0 && (
                <div className="row-between small"><span>{t('Yetkazib berish')}</span><span>{formatPrice(o.delivery_price)}</span></div>
              )}
            </div>
            <div className="row-between">
              <span className="muted small">{t("To'lov: {p}", { p: paymentTitle(o.payment_method) })}</span>
              <strong>{formatPrice(o.total)}</strong>
            </div>
          </div>
        ))}
      {hasMore && (
        <div className="more-orders">
          <span className="muted small">{t("{shown} / {total} ta buyurtma ko'rsatilmoqda", { shown: orders.length, total: count })}</span>
          <button className="btn btn-outline" onClick={more} disabled={loadingMore}>
            {loadingMore ? t('Yuklanmoqda...') : t("Ko'proq ko'rish")}
          </button>
        </div>
      )}
    </div>
  )
}
