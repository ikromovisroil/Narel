import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { BoxIcon, CartIcon, HeartIcon, LogoutIcon, UserIcon } from '../components/Icons'
import PhoneVerify from '../components/PhoneVerify'
import { dateLocale, t } from '../i18n'
import { fieldErrorsOf } from '../phone'
import { useStore } from '../store'
import { Field } from './Auth'

const FIELDS = ['first_name', 'last_name', 'address', 'email']
const fromUser = u => ({
  first_name: u?.first_name || '', last_name: u?.last_name || '', address: u?.address || '', email: u?.email || '',
})
const initials = u => ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || '👤'

// Profil to'liqligi: nimalar to'ldirilmagan
function completeness(user) {
  const items = [
    [!!(user.first_name && user.last_name), t('Ism va familiya')],
    [!!user.phone, t('Telefon')],
    [!!user.address, t('Yetkazish manzili')],
    [!!user.email, 'Email'],
  ]
  return { percent: Math.round((items.filter(i => i[0]).length / items.length) * 100), missing: items.filter(i => !i[0]).map(i => i[1]) }
}

// Mijoz profili: ism, telefon (SMS kod bilan), manzil va email. Login/parol yo'q — kirish telefon orqali.
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
  const [changingPhone, setChangingPhone] = useState(false)

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
    setForm({ ...form, [k]: e.target.value })
    setSaved(false)
    if (errors[k]) setErrors({ ...errors, [k]: '' })
  }

  const validate = () => {
    const errs = {}
    if (!form.first_name.trim()) errs.first_name = t('Ismingizni kiriting.')
    if (!form.last_name.trim()) errs.last_name = t('Familiyangizni kiriting.')
    if (form.address.trim() && form.address.trim().length < 5) errs.address = t("Manzilni to'liq kiriting.")
    if (form.email.trim() && !/^\S+@\S+\.\S+$/.test(form.email.trim())) errs.email = t("Emailni to'g'ri kiriting.")
    setErrors(errs)
    return !Object.keys(errs).length
  }

  const goNext = () => { if (next?.startsWith('/') && !next.startsWith('//')) navigate(next) }

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (!validate()) return
    setSending(true)
    try {
      setUser(await api('/auth/me/', { method: 'PATCH', body: form }))
      setSaved(true)
      if (user.phone) goNext()
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
  const { percent, missing } = completeness(user)
  const fullName = `${user.first_name} ${user.last_name}`.trim()
  const last = orders?.results?.[0]

  return (
    <div className="profile-page">
      <aside className="profile-side">
        <div className="pcard profile-hero">
          <div className="avatar">{initials(user)}</div>
          <b className="hero-name">{fullName || t('Ismingizni kiriting')}</b>
          <span className="muted small">{user.phone || user.email}</span>
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
          <a href="#phone">📱 {t('Telefon raqami')}</a>
          <a href="#address">📍 {t('Yetkazish manzili')}</a>
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

        <section className="pcard" id="phone">
          <div className="pcard-head">
            <h2>📱 {t('Telefon raqami')}</h2>
            {user.phone && !changingPhone && (
              <button type="button" className="link" onClick={() => setChangingPhone(true)}>{t("O'zgartirish")}</button>
            )}
          </div>
          {user.phone && !changingPhone ? (
            <div className="phone-current"><b>{user.phone}</b><span className="muted small">{t('Shu raqam bilan saytga kirasiz.')}</span></div>
          ) : (
            <>
              <span className="muted small">
                {user.phone ? t('Yangi raqamga SMS kod yuboramiz — tasdiqlangach, saytga shu raqam bilan kirasiz.')
                  : t('Buyurtma berish uchun telefon raqamingizni SMS kod bilan tasdiqlang.')}
              </span>
              <PhoneVerify
                onDone={() => { setChangingPhone(false); if (fullName) goNext() }}
                onCancel={user.phone ? () => setChangingPhone(false) : undefined}
              />
            </>
          )}
        </section>

        <form onSubmit={submit} noValidate className="profile-form">
          <section className="pcard" id="info">
            <h2>👤 {t("Shaxsiy ma'lumotlar")}</h2>
            <div className="pgrid">
              <Field label={t('Ism')} required error={errors.first_name}>{input('first_name', { autoComplete: 'given-name' })}</Field>
              <Field label={t('Familiya')} required error={errors.last_name}>{input('last_name', { autoComplete: 'family-name' })}</Field>
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

          <div className={`save-bar ${dirty ? 'dirty' : ''}`}>
            {error && <span className="error">{error}</span>}
            {saved && !dirty && <span className="ok">✓ {t('Saqlandi')}</span>}
            {dirty && <span className="muted small">{t("O'zgarishlar saqlanmagan")}</span>}
            {dirty && <button type="button" className="btn btn-light" onClick={() => { setForm(fromUser(user)); setErrors({}) }}>{t('Bekor qilish')}</button>}
            <button className="btn" disabled={sending || !dirty}>{sending ? t('Saqlanmoqda...') : t('Saqlash')}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
