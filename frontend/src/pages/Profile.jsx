import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { BoxIcon, CartIcon, HeartIcon, LogoutIcon, UserIcon } from '../components/Icons'
import { dateLocale, t } from '../i18n'
import { fieldErrorsOf, formatPhone, phoneOk } from '../phone'
import { useStore } from '../store'
import { Field } from './Auth'

const FIELDS = ['first_name', 'last_name', 'phone', 'address', 'username', 'email']
const fromUser = u => ({
  first_name: u?.first_name || '', last_name: u?.last_name || '',
  phone: u?.phone || '+998 ', address: u?.address || '', username: u?.username || '', email: u?.email || '',
})
const initials = u => ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || u.username[0].toUpperCase()

// Profil to'liqligi: nimalar to'ldirilmagan
function useCompleteness(user) {
  const items = [
    [!!(user.first_name && user.last_name), t('Ism va familiya')],
    [phoneOk(user.phone), t('Telefon')],
    [!!user.address, t('Yetkazish manzili')],
    [!!user.email, 'Email'],
  ]
  return { percent: Math.round((items.filter(i => i[0]).length / items.length) * 100), missing: items.filter(i => !i[0]).map(i => i[1]) }
}

// Parolni o'zgartirish
function PasswordCard({ hasPassword, onSet }) {
  const [form, setForm] = useState({ old_password: '', new_password: '', repeat: '' })
  const [errors, setErrors] = useState({})
  const [show, setShow] = useState(false)
  const [done, setDone] = useState(false)
  const [sending, setSending] = useState(false)

  const set = k => e => {
    setForm({ ...form, [k]: e.target.value })
    setDone(false)
    if (errors[k]) setErrors({ ...errors, [k]: '' })
  }

  const submit = async e => {
    e.preventDefault()
    const errs = {}
    if (hasPassword && !form.old_password) errs.old_password = t('Joriy parolni kiriting.')
    if (form.new_password.length < 8) errs.new_password = t("Parol kamida 8 ta belgidan iborat bo'lsin.")
    else if (form.new_password !== form.repeat) errs.repeat = t('Parollar bir xil emas.')
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSending(true)
    try {
      await api('/auth/password/', { method: 'POST', body: { old_password: form.old_password, new_password: form.new_password } })
      setForm({ old_password: '', new_password: '', repeat: '' })
      setDone(true)
      onSet?.()
    } catch (err) {
      const fe = fieldErrorsOf(err, ['old_password', 'new_password'])
      setErrors(Object.keys(fe).length ? fe : { new_password: errorText(err) })
    } finally {
      setSending(false)
    }
  }

  const type = show ? 'text' : 'password'
  return (
    <form className="pcard" id="security" onSubmit={submit} noValidate>
      <div className="pcard-head">
        <h2>🔒 {hasPassword ? t("Parolni o'zgartirish") : t("Parol o'rnatish")}</h2>
        <label className="show-pass"><input type="checkbox" checked={show} onChange={e => setShow(e.target.checked)} /> {t("Ko'rsatish")}</label>
      </div>
      {!hasPassword && (
        <p className="muted small">{t("Siz Google orqali kirgansiz. Parol o'rnatsangiz, login yoki email va parol bilan ham kira olasiz.")}</p>
      )}
      <div className="pgrid">
        {hasPassword && (
          <>
            <Field label={t('Joriy parol')} required error={errors.old_password}>
              <input type={type} autoComplete="current-password" value={form.old_password} onChange={set('old_password')}
                     className={errors.old_password ? 'invalid' : ''} />
            </Field>
            <span className="pgrid-gap" />
          </>
        )}
        <Field label={t('Yangi parol')} required error={errors.new_password}>
          <input type={type} autoComplete="new-password" value={form.new_password} onChange={set('new_password')}
                 className={errors.new_password ? 'invalid' : ''} />
        </Field>
        <Field label={t('Yangi parolni takrorlang')} required error={errors.repeat}>
          <input type={type} autoComplete="new-password" value={form.repeat} onChange={set('repeat')}
                 className={errors.repeat ? 'invalid' : ''} />
        </Field>
      </div>
      <p className="muted small">{t("Kamida 8 ta belgi; faqat raqamlardan iborat yoki juda oddiy parol qabul qilinmaydi.")}</p>
      <div className="pcard-foot">
        {done && <span className="ok">✓ {t("Parol o'zgartirildi")}</span>}
        <button className="btn" disabled={sending}>
          {sending ? t('Saqlanmoqda...') : hasPassword ? t("Parolni o'zgartirish") : t("Parol o'rnatish")}
        </button>
      </div>
    </form>
  )
}

// Mijoz profili: shaxsiy ma'lumotlar, manzil, kirish ma'lumotlari va parol
export default function Profile() {
  const { user, setUser, logout, favorites, cartCount } = useStore()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next')
  const [form, setForm] = useState(fromUser(user))
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [sending, setSending] = useState(false)
  const [orders, setOrders] = useState(null)

  useEffect(() => { setForm(fromUser(user)) }, [user])
  useEffect(() => {
    if (user) api('/orders/').then(r => setOrders(r)).catch(() => setOrders(null))
  }, [user])

  if (!user) {
    return (
      <div className="empty">
        <h2>{t("Profilni ko'rish uchun tizimga kiring")}</h2>
        <Link className="btn" to="/login?next=/profile">{t('Kirish')}</Link>
      </div>
    )
  }

  const set = k => e => {
    setForm({ ...form, [k]: k === 'phone' ? formatPhone(e.target.value) : e.target.value })
    setSaved(false)
    if (errors[k]) setErrors({ ...errors, [k]: '' })
  }

  const validate = () => {
    const errs = {}
    if (!form.first_name.trim()) errs.first_name = t('Ismingizni kiriting.')
    if (!form.last_name.trim()) errs.last_name = t('Familiyangizni kiriting.')
    if (!phoneOk(form.phone)) errs.phone = t("Telefon raqamini to'liq kiriting: +998 XX XXX XX XX.")
    if (form.address.trim() && form.address.trim().length < 5) errs.address = t("Manzilni to'liq kiriting.")
    if (!form.username.trim()) errs.username = t('Login kiriting.')
    if (form.email.trim() && !/^\S+@\S+\.\S+$/.test(form.email.trim())) errs.email = t("Emailni to'g'ri kiriting.")
    setErrors(errs)
    return !Object.keys(errs).length
  }

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (!validate()) return
    setSending(true)
    try {
      setUser(await api('/auth/me/', { method: 'PATCH', body: form }))
      setSaved(true)
      if (next?.startsWith('/') && !next.startsWith('//')) navigate(next)
    } catch (err) {
      const errs = fieldErrorsOf(err, FIELDS)
      setErrors(errs)
      if (!Object.keys(errs).length) setError(errorText(err))
    } finally {
      setSending(false)
    }
  }

  const input = (k, props = {}) => (
    <input value={form[k]} onChange={set(k)} className={errors[k] ? 'invalid' : ''} {...props} />
  )
  const dirty = FIELDS.some(k => (form[k] || '').trim() !== (fromUser(user)[k] || '').trim())
  const { percent, missing } = useCompleteness(user)
  const fullName = `${user.first_name} ${user.last_name}`.trim() || user.username
  const last = orders?.results?.[0]

  return (
    <div className="profile-page">
      <aside className="profile-side">
        <div className="pcard profile-hero">
          <div className="avatar">{initials(user)}</div>
          <b className="hero-name">{fullName}</b>
          <span className="muted small">{user.phone || user.email || user.username}</span>
          {user.date_joined && (
            <span className="muted small">
              {t("A'zo bo'lgan sana: {date}", { date: new Date(user.date_joined).toLocaleDateString(dateLocale()) })}
            </span>
          )}
          <div className="completeness">
            <div className="row-between small"><span>{t("Profil to'ldirilgan")}</span><b>{percent}%</b></div>
            <div className="bar"><i style={{ width: `${percent}%` }} /></div>
            {missing.length > 0 && <span className="muted small">{t("Qo'shing: {list}", { list: missing.join(', ') })}</span>}
          </div>
        </div>

        <div className="pstats">
          <Link to="/orders" className="pstat"><BoxIcon size={20} /><b>{orders?.count ?? '—'}</b><span>{t('Buyurtmalar')}</span></Link>
          <Link to="/favorites" className="pstat"><HeartIcon size={20} /><b>{favorites.length}</b><span>{t('Sevimlilar')}</span></Link>
          <Link to="/cart" className="pstat"><CartIcon size={20} /><b>{cartCount}</b><span>{t('Savat')}</span></Link>
        </div>

        <nav className="pcard pnav">
          <a href="#info"><UserIcon size={18} /> {t("Shaxsiy ma'lumotlar")}</a>
          <a href="#address">📍 {t('Yetkazish manzili')}</a>
          <a href="#account">🔑 {t("Kirish ma'lumotlari")}</a>
          <a href="#security">🔒 {t("Parolni o'zgartirish")}</a>
          <button type="button" className="danger" onClick={() => { logout(); navigate('/') }}>
            <LogoutIcon size={18} /> {t('Chiqish')}
          </button>
        </nav>
      </aside>

      <div className="profile-main">
        <h1 className="page-title">{t('Profil')}</h1>

        {last && (
          <Link to="/orders" className="pcard last-order">
            <span className="muted small">{t('Oxirgi buyurtma')}</span>
            <b>{t('Buyurtma #{id}', { id: last.id })} · {last.status_display}</b>
            <span className="muted small">{new Date(last.created_at).toLocaleDateString(dateLocale())}</span>
          </Link>
        )}

        <form onSubmit={submit} noValidate className="profile-form">
          <section className="pcard" id="info">
            <h2>👤 {t("Shaxsiy ma'lumotlar")}</h2>
            <div className="pgrid">
              <Field label={t('Ism')} required error={errors.first_name}>{input('first_name', { autoComplete: 'given-name' })}</Field>
              <Field label={t('Familiya')} required error={errors.last_name}>{input('last_name', { autoComplete: 'family-name' })}</Field>
              <Field label={t('Telefon')} required error={errors.phone}>
                {input('phone', { type: 'tel', inputMode: 'tel', autoComplete: 'tel', placeholder: '+998 90 123 45 67' })}
              </Field>
              <Field label="Email" error={errors.email}>{input('email', { type: 'email', autoComplete: 'email', placeholder: 'name@mail.uz' })}</Field>
            </div>
          </section>

          <section className="pcard" id="address">
            <h2>📍 {t('Yetkazish manzili')}</h2>
            <Field label={t('Manzil')} error={errors.address}>
              <textarea rows={2} value={form.address} onChange={set('address')} className={errors.address ? 'invalid' : ''}
                        placeholder={t("Shahar, tuman, ko'cha, uy")} autoComplete="street-address" />
            </Field>
            <p className="muted small">{t("Ism, telefon va manzil buyurtma berishda avtomatik qo'yiladi.")}</p>
          </section>

          <section className="pcard" id="account">
            <h2>🔑 {t("Kirish ma'lumotlari")}</h2>
            <div className="pgrid">
              <Field label={t('Login')} required error={errors.username}>{input('username', { autoComplete: 'username' })}</Field>
            </div>
            <p className="muted small">{t("Saytga login, email yoki telefon raqami bilan kirishingiz mumkin.")}</p>
          </section>

          <div className={`save-bar ${dirty ? 'dirty' : ''}`}>
            {error && <span className="error">{error}</span>}
            {saved && !dirty && <span className="ok">✓ {t('Saqlandi')}</span>}
            {dirty && <span className="muted small">{t("O'zgarishlar saqlanmagan")}</span>}
            {dirty && <button type="button" className="btn btn-light" onClick={() => { setForm(fromUser(user)); setErrors({}) }}>{t('Bekor qilish')}</button>}
            <button className="btn" disabled={sending || !dirty}>{sending ? t('Saqlanmoqda...') : t('Saqlash')}</button>
          </div>
        </form>

        <PasswordCard hasPassword={user.has_password !== false} onSet={() => setUser({ ...user, has_password: true })} />
      </div>
    </div>
  )
}
