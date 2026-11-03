import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, errorText, formatPrice } from '../api'
import { t } from '../i18n'
import { useStore } from '../store'

export default function Checkout() {
  const { user, cart, cartTotal, clearCart, paymentMethods, installmentMonths, monthly } = useStore()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: user ? `${user.first_name} ${user.last_name}`.trim() : '',
    phone: '+998', address: '', note: '',
    payment_method: '', delivery_method: 'courier',
  })
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(null)

  if (done) {
    return (
      <div className="empty">
        <div style={{ fontSize: 48 }}>✅</div>
        <h2>{t('Buyurtma #{id} qabul qilindi!', { id: done.id })}</h2>
        <p className="muted">{t("Operatorimiz tez orada {phone} raqamiga qo'ng'iroq qiladi.", { phone: done.phone })}</p>
        <Link className="btn" to="/orders">{t('Buyurtmalarim')}</Link>
      </div>
    )
  }
  if (!user) {
    return (
      <div className="empty">
        <h2>{t('Buyurtma berish uchun tizimga kiring')}</h2>
        <Link className="btn" to="/login?next=/checkout">{t('Kirish')}</Link>
      </div>
    )
  }
  if (!cart.length) return <Navigate to="/cart" />

  const set = k => e => setForm({ ...form, [k]: e.target.value })
  // Faqat admin yoqqan usullar; tanlangani o'chirilgan bo'lsa birinchisi olinadi
  const payment = paymentMethods.some(m => m.code === form.payment_method)
    ? form.payment_method : paymentMethods[0]?.code
  const submit = async e => {
    e.preventDefault()
    setError(''); setSending(true)
    try {
      const order = await api('/orders/', {
        method: 'POST',
        body: { ...form, payment_method: payment, cart: cart.map(i => ({ product: i.id, quantity: i.qty })) },
      })
      clearCart()
      setDone(order)
      window.scrollTo(0, 0)
    } catch (err) {
      if (err.status === 401) navigate('/login?next=/checkout')
      setError(errorText(err))
    } finally {
      setSending(false)
    }
  }

  const deliveries = [
    ['courier', 'Kuryer orqali', "Toshkent bo'ylab bepul"],
    ['pickup', "Do'kondan olib ketish", 'Bugunoq'],
  ]
  const paymentSub = m => (m.code === 'installment' && installmentMonths
    ? t('{sum} × {n} oy', { sum: formatPrice(monthly(cartTotal)), n: installmentMonths })
    : m.description)

  return (
    <div>
      <h1 className="page-title">{t('Buyurtmani rasmiylashtirish')}</h1>
      <form className="cart" onSubmit={submit}>
        <div className="form-card">
          <h3>{t('Qabul qiluvchi')}</h3>
          <div className="form-row">
            <label>{t('F.I.Sh.')}<input required value={form.full_name} onChange={set('full_name')} /></label>
            <label>{t('Telefon')}<input required value={form.phone} onChange={set('phone')} /></label>
          </div>

          <h3>{t('Yetkazib berish')}</h3>
          <div className="choices">
            {deliveries.map(([v, title, sub]) => (
              <label key={v} className={`choice ${form.delivery_method === v ? 'on' : ''}`}>
                <input type="radio" name="delivery" value={v} checked={form.delivery_method === v}
                       onChange={set('delivery_method')} />
                <b>{t(title)}</b><span className="muted small">{t(sub)}</span>
              </label>
            ))}
          </div>
          {form.delivery_method === 'courier' && (
            <label>{t('Manzil')}<textarea required rows={2} value={form.address} onChange={set('address')}
                                         placeholder={t("Shahar, tuman, ko'cha, uy")} /></label>
          )}

          <h3>{t("To'lov usuli")}</h3>
          {paymentMethods.length ? (
            <div className="choices">
              {paymentMethods.map(m => (
                <label key={m.code} className={`choice ${payment === m.code ? 'on' : ''}`}>
                  <input type="radio" name="payment" value={m.code} checked={payment === m.code}
                         onChange={set('payment_method')} />
                  <span className="choice-head">
                    {m.logo && <img src={m.logo} alt="" className="pay-logo" />}
                    <b>{m.title}</b>
                  </span>
                  <span className="muted small">{paymentSub(m)}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="error">{t("Hozircha to'lov usullari mavjud emas. Iltimos, keyinroq urinib ko'ring.")}</div>
          )}
          <label>{t('Izoh')}<textarea rows={2} value={form.note} onChange={set('note')} /></label>
          {error && <div className="error">{error}</div>}
        </div>

        <div className="buy-box">
          <h3>{t('Buyurtmangiz')}</h3>
          {cart.map(i => (
            <div key={i.id} className="row-between small">
              <span>{i.name} × {i.qty}</span><span>{formatPrice(i.price * i.qty)}</span>
            </div>
          ))}
          <hr />
          <div className="row-between big"><span>{t('Jami')}</span><strong>{formatPrice(cartTotal)}</strong></div>
          <button className="btn btn-lg" disabled={sending || !payment}>{sending ? t('Yuborilmoqda...') : t('Buyurtma berish')}</button>
        </div>
      </form>
    </div>
  )
}
