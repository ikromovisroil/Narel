import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, errorText, formatPrice } from '../api'
import { useStore } from '../store'

export default function Checkout() {
  const { user, cart, cartTotal, clearCart } = useStore()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: user ? `${user.first_name} ${user.last_name}`.trim() : '',
    phone: '+998', address: '', note: '',
    payment_method: 'cash', delivery_method: 'courier',
  })
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(null)

  if (done) {
    return (
      <div className="empty">
        <div style={{ fontSize: 48 }}>✅</div>
        <h2>Buyurtma #{done.id} qabul qilindi!</h2>
        <p className="muted">Operatorimiz tez orada {done.phone} raqamiga qo'ng'iroq qiladi.</p>
        <Link className="btn" to="/orders">Buyurtmalarim</Link>
      </div>
    )
  }
  if (!user) {
    return (
      <div className="empty">
        <h2>Buyurtma berish uchun tizimga kiring</h2>
        <Link className="btn" to="/login?next=/checkout">Kirish</Link>
      </div>
    )
  }
  if (!cart.length) return <Navigate to="/cart" />

  const set = k => e => setForm({ ...form, [k]: e.target.value })
  const submit = async e => {
    e.preventDefault()
    setError(''); setSending(true)
    try {
      const order = await api('/orders/', {
        method: 'POST',
        body: { ...form, cart: cart.map(i => ({ product: i.id, quantity: i.qty })) },
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

  return (
    <div>
      <h1 className="page-title">Buyurtmani rasmiylashtirish</h1>
      <form className="cart" onSubmit={submit}>
        <div className="form-card">
          <h3>Qabul qiluvchi</h3>
          <div className="form-row">
            <label>F.I.Sh.<input required value={form.full_name} onChange={set('full_name')} /></label>
            <label>Telefon<input required value={form.phone} onChange={set('phone')} /></label>
          </div>

          <h3>Yetkazib berish</h3>
          <div className="choices">
            {[['courier', 'Kuryer orqali', 'Toshkent bo\'ylab bepul'], ['pickup', 'Do\'kondan olib ketish', 'Bugunoq']]
              .map(([v, t, s]) => (
                <label key={v} className={`choice ${form.delivery_method === v ? 'on' : ''}`}>
                  <input type="radio" name="delivery" value={v} checked={form.delivery_method === v}
                         onChange={set('delivery_method')} />
                  <b>{t}</b><span className="muted small">{s}</span>
                </label>
              ))}
          </div>
          {form.delivery_method === 'courier' && (
            <label>Manzil<textarea required rows={2} value={form.address} onChange={set('address')}
                                   placeholder="Shahar, tuman, ko'cha, uy" /></label>
          )}

          <h3>To'lov usuli</h3>
          <div className="choices">
            {[['cash', 'Naqd pul', 'Qabul qilganda'], ['card', 'Karta orqali', 'Uzcard / Humo'],
              ['installment', 'Muddatli to\'lov', `${formatPrice(cartTotal / 12)} × 12 oy`]]
              .map(([v, t, s]) => (
                <label key={v} className={`choice ${form.payment_method === v ? 'on' : ''}`}>
                  <input type="radio" name="payment" value={v} checked={form.payment_method === v}
                         onChange={set('payment_method')} />
                  <b>{t}</b><span className="muted small">{s}</span>
                </label>
              ))}
          </div>
          <label>Izoh<textarea rows={2} value={form.note} onChange={set('note')} /></label>
          {error && <div className="error">{error}</div>}
        </div>

        <div className="buy-box">
          <h3>Buyurtmangiz</h3>
          {cart.map(i => (
            <div key={i.id} className="row-between small">
              <span>{i.name} × {i.qty}</span><span>{formatPrice(i.price * i.qty)}</span>
            </div>
          ))}
          <hr />
          <div className="row-between big"><span>Jami</span><strong>{formatPrice(cartTotal)}</strong></div>
          <button className="btn btn-lg" disabled={sending}>{sending ? 'Yuborilmoqda...' : 'Buyurtma berish'}</button>
        </div>
      </form>
    </div>
  )
}
