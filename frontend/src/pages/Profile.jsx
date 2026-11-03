import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { t } from '../i18n'
import { fieldErrorsOf, formatPhone, phoneOk } from '../phone'
import { useStore } from '../store'
import { Field } from './Auth'

const FIELDS = ['first_name', 'last_name', 'phone', 'username', 'email']
const fromUser = u => ({
  first_name: u?.first_name || '', last_name: u?.last_name || '',
  phone: u?.phone || '+998 ', username: u?.username || '', email: u?.email || '',
})

// Mijoz profili: FISH, telefon, login va emailni o'zgartirish
export default function Profile() {
  const { user, setUser } = useStore()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next')
  const [form, setForm] = useState(fromUser(user))
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [sending, setSending] = useState(false)

  useEffect(() => { setForm(fromUser(user)) }, [user])

  if (!user) {
    return (
      <div className="empty">
        <h2>{t('Profilni ko\'rish uchun tizimga kiring')}</h2>
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

  return (
    <form className="auth profile" onSubmit={submit} noValidate>
      <h1>{t('Profil')}</h1>
      <div className="form-row">
        <Field label={t('Ism')} required error={errors.first_name}>{input('first_name', { autoComplete: 'given-name' })}</Field>
        <Field label={t('Familiya')} required error={errors.last_name}>{input('last_name', { autoComplete: 'family-name' })}</Field>
      </div>
      <Field label={t('Telefon')} required error={errors.phone}>
        {input('phone', { type: 'tel', inputMode: 'tel', autoComplete: 'tel', placeholder: '+998 90 123 45 67' })}
      </Field>
      <Field label={t('Login')} required error={errors.username}>{input('username', { autoComplete: 'username' })}</Field>
      <Field label="Email" error={errors.email}>{input('email', { type: 'email', autoComplete: 'email' })}</Field>
      <p className="muted small">{t("Saytga login, email yoki telefon raqami bilan kirishingiz mumkin.")}</p>
      {error && <div className="error">{error}</div>}
      {saved && <div className="ok">✓ {t('Saqlandi')}</div>}
      <button className="btn btn-lg" disabled={sending}>{sending ? t('Saqlanmoqda...') : t('Saqlash')}</button>
      <Link to="/orders" className="muted small">{t('Buyurtmalarim')} →</Link>
    </form>
  )
}
