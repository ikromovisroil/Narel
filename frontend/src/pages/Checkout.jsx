import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, errorText, formatPrice } from '../api'
import StoreInfo from '../components/StoreInfo'
import { phoneOk } from '../phone'
import { t } from '../i18n'
import { useStore } from '../store'

const fmtDate = d => new Date(d).toLocaleDateString('ru-RU')


export default function Checkout() {
  const { user, cart, cartTotal, clearCart, paymentMethods, installmentMonths, monthly, storeInfo } = useStore()
  const navigate = useNavigate()
  const [form, setForm] = useState({ address: '', note: '', payment_method: '', delivery_method: '', pickup_branch: null })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(null)

  if (done) {
    return (
      <div className="empty">
        <div style={{ fontSize: 48 }}>✅</div>
        <h2>{t('Buyurtma #{id} qabul qilindi!', { id: done.id })}</h2>
        <p className="muted">{t("Operatorimiz tez orada {phone} raqamiga qo'ng'iroq qiladi.", { phone: done.phone })}</p>
        {done.delivery_method === 'courier' && done.expected_date && (
          <p className="expected">🚚 {t('Taxminiy yetkazish: {date}', { date: fmtDate(done.expected_date) })}</p>
        )}
        {done.delivery_method === 'pickup' && (
          <StoreInfo title={t('Buyurtmani shu yerdan olib ketasiz')} info={done.pickup_branch_info} />
        )}
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

  const set = k => e => {
    setForm({ ...form, [k]: k === 'pickup_branch' ? Number(e.target.value) : e.target.value })
    if (fieldErrors[k]) setFieldErrors({ ...fieldErrors, [k]: '' })
  }

  // FISH va telefon — profildan (registratsiyada kiritilgan)
  const fullName = `${user.first_name} ${user.last_name}`.trim()
  const profileOk = !!fullName && phoneOk(user.phone)

  // Manzil va (olib ketishda) filial majburiy — backend ham tekshiradi
  const validate = () => {
    const errs = {}
    if (form.address.trim().length < 5) errs.address = t("Manzilni to'liq kiriting.")
    if (delivery === 'pickup' && !branch) errs.pickup_branch = t('Buyurtmani olib ketadigan filialni tanlang.')
    setFieldErrors(errs)
    return !Object.keys(errs).length
  }
  // Faqat admin yoqqan usullar; tanlangani o'chirilgan bo'lsa birinchisi olinadi
  const payment = paymentMethods.some(m => m.code === form.payment_method)
    ? form.payment_method : paymentMethods[0]?.code

  // Yetkazish usullari — admin Sozlamalaridan
  const deliveryOn = storeInfo?.delivery_enabled
  const pickupOn = storeInfo?.pickup_enabled
  const deliveryPrice = Number(storeInfo?.delivery_price || 0)
  const branches = storeInfo?.branches || []
  // Bitta filial bo'lsa — o'zi tanlanadi
  const branch = branches.find(b => b.id === form.pickup_branch) || (branches.length === 1 ? branches[0] : null)
  const deliveries = [
    deliveryOn && {
      code: 'courier', title: t('Kuryer orqali'),
      sub: `${deliveryPrice ? formatPrice(deliveryPrice) : t('Bepul')}${storeInfo.delivery_note ? ` · ${storeInfo.delivery_note}` : ''}`,
    },
    pickupOn && {
      code: 'pickup', title: t("Do'kondan olib ketish"),
      sub: `${t('Bepul')} · ${branches.length > 1 ? t('{n} ta filial', { n: branches.length }) : branches[0]?.address || ''}`,
    },
  ].filter(Boolean)
  const delivery = deliveries.some(d => d.code === form.delivery_method) ? form.delivery_method : deliveries[0]?.code
  const fee = delivery === 'courier' ? deliveryPrice : 0

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (!validate()) return
    setSending(true)
    try {
      const order = await api('/orders/', {
        method: 'POST',
        body: {
          ...form, payment_method: payment, delivery_method: delivery,
          pickup_branch: delivery === 'pickup' ? branch?.id : null,
          cart: cart.map(i => ({ product: i.id, quantity: i.qty })),
        },
      })
      clearCart()
      setDone(order)
      window.scrollTo(0, 0)
    } catch (err) {
      if (err.status === 401) navigate('/login?next=/checkout')
      const d = err?.data || {}
      if (d.address || d.pickup_branch) {
        setFieldErrors({ address: [].concat(d.address || [])[0] || '', pickup_branch: [].concat(d.pickup_branch || [])[0] || '' })
      } else {
        setError(errorText(err))
      }
    } finally {
      setSending(false)
    }
  }

  const paymentSub = m => (m.code === 'installment' && installmentMonths
    ? t('{sum} × {n} oy', { sum: formatPrice(monthly(cartTotal + fee)), n: installmentMonths })
    : m.description)

  return (
    <div>
      <h1 className="page-title">{t('Buyurtmani rasmiylashtirish')}</h1>
      <form className="cart" onSubmit={submit} noValidate>
        <div className="form-card">
          <h3>{t('Qabul qiluvchi')}</h3>
          {profileOk ? (
            <div className="recipient">
              <div><b>{fullName}</b><span className="muted">{user.phone}</span></div>
              <Link to="/profile?next=/checkout" className="small">{t("O'zgartirish")}</Link>
            </div>
          ) : (
            <div className="notice">
              <b>{t("Profilingizda ism-familiya yoki telefon yo'q")}</b>
              <span>{t("Buyurtma berish uchun profilni to'ldiring — keyingi safar qayta so'ralmaydi.")}</span>
              <Link className="btn" to="/profile?next=/checkout">{t("Profilni to'ldirish")}</Link>
            </div>
          )}

          <h3>{t('Yetkazib berish')}</h3>
          {storeInfo && !deliveryOn && (
            <div className="notice">
              <b>{t("Hozircha yetkazib berish yo'q")}</b>
              <span>{t("Buyurtmani do'kondan olib ketishingiz mumkin. Savollar bo'lsa, qo'ng'iroq qiling:")}</span>
              <StoreInfo />
            </div>
          )}
          <div className="choices">
            {deliveries.map(d => (
              <label key={d.code} className={`choice ${delivery === d.code ? 'on' : ''}`}>
                <input type="radio" name="delivery" value={d.code} checked={delivery === d.code}
                       onChange={set('delivery_method')} />
                <b>{d.title}</b><span className="muted small">{d.sub}</span>
              </label>
            ))}
          </div>
          <label>
            <span>{delivery === 'courier' ? t('Yetkazish manzili') : t('Manzilingiz')} <span className="req">*</span></span>
            <textarea required rows={2} value={form.address} onChange={set('address')}
                      className={fieldErrors.address ? 'invalid' : ''} placeholder={t("Shahar, tuman, ko'cha, uy")} />
            {fieldErrors.address && <span className="field-error">{fieldErrors.address}</span>}
          </label>
          {delivery === 'pickup' && (
            <div className="branch-pick">
              <span className="label-text">{t('Qaysi filialdan olib ketasiz?')} <span className="req">*</span></span>
              <div className="choices branches">
                {branches.map(b => (
                  <label key={b.id} className={`choice ${branch?.id === b.id ? 'on' : ''}`}>
                    <input type="radio" name="branch" value={b.id} checked={branch?.id === b.id} onChange={set('pickup_branch')} />
                    <b>{b.name}</b>
                    <span className="small">📍 {b.address}</span>
                    <span className="muted small">☎ {b.phone}{b.working_hours ? ` · ${b.working_hours}` : ''}</span>
                    {b.map_url && (
                      <a className="small" href={b.map_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}>
                        {t("Xaritada ko'rish")}
                      </a>
                    )}
                  </label>
                ))}
              </div>
              {fieldErrors.pickup_branch && <span className="field-error">{fieldErrors.pickup_branch}</span>}
            </div>
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
          <div className="row-between small">
            <span>{delivery === 'pickup' ? t("Do'kondan olib ketish") : t('Yetkazib berish')}</span>
            <span className={fee ? '' : 'ok'}>{fee ? formatPrice(fee) : t('Bepul')}</span>
          </div>
          <div className="row-between big"><span>{t('Jami')}</span><strong>{formatPrice(cartTotal + fee)}</strong></div>
          <button className="btn btn-lg" disabled={sending || !payment || !delivery || !profileOk}>
            {sending ? t('Yuborilmoqda...') : t('Buyurtma berish')}
          </button>
        </div>
      </form>
    </div>
  )
}
