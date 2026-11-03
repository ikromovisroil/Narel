import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import GoogleButton from '../components/GoogleButton'
import { t } from '../i18n'
import { fieldErrorsOf, formatPhone, phoneOk } from '../phone'
import { useStore } from '../store'

function useNext() {
  const [params] = useSearchParams()
  const next = params.get('next') || '/'
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

// Maydon: sarlavha, input va xato matni
export function Field({ label, required, error, children }) {
  return (
    <label>
      <span>{label}{required && <> <span className="req">*</span></>}</span>
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

export function Login() {
  const { login } = useStore()
  const navigate = useNavigate()
  const next = useNext()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')

  const submit = async e => {
    e.preventDefault()
    setError('')
    try {
      await login(form.username, form.password)
      navigate(next)
    } catch (err) {
      setError(err.status === 401 ? t("Login yoki parol noto'g'ri") : errorText(err))
    }
  }

  return (
    <form className="auth" onSubmit={submit}>
      <h1>{t('Kirish')}</h1>
      <label>{t('Login, email yoki telefon')}<input required autoComplete="username" value={form.username}
                         onChange={e => setForm({ ...form, username: e.target.value })} /></label>
      <label>{t('Parol')}<input required type="password" autoComplete="current-password" value={form.password}
                         onChange={e => setForm({ ...form, password: e.target.value })} /></label>
      {error && <div className="error">{error}</div>}
      <button className="btn btn-lg">{t('Kirish')}</button>
      <GoogleButton next={next} />
      <p className="muted">{t("Hisobingiz yo'qmi?")} <Link to={`/register?next=${encodeURIComponent(next)}`}>{t("Ro'yxatdan o'tish")}</Link></p>
    </form>
  )
}

const FIELDS = ['first_name', 'last_name', 'phone', 'username', 'email', 'password']

export function Register() {
  const { login } = useStore()
  const navigate = useNavigate()
  const next = useNext()
  const [mode, setMode] = useState('email') // email | login
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '+998 ', username: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  const set = k => e => {
    setForm({ ...form, [k]: k === 'phone' ? formatPhone(e.target.value) : e.target.value })
    if (errors[k]) setErrors({ ...errors, [k]: '' })
  }

  const validate = () => {
    const errs = {}
    if (!form.first_name.trim()) errs.first_name = t('Ismingizni kiriting.')
    if (!form.last_name.trim()) errs.last_name = t('Familiyangizni kiriting.')
    if (!phoneOk(form.phone)) errs.phone = t("Telefon raqamini to'liq kiriting: +998 XX XXX XX XX.")
    if (mode === 'email' && !/^\S+@\S+\.\S+$/.test(form.email.trim())) errs.email = t("Emailni to'g'ri kiriting.")
    if (mode === 'login' && !form.username.trim()) errs.username = t('Login kiriting.')
    if (form.password.length < 8) errs.password = t("Parol kamida 8 ta belgidan iborat bo'lsin.")
    setErrors(errs)
    return !Object.keys(errs).length
  }

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (!validate()) return
    const body = { ...form, ...(mode === 'email' ? { username: '' } : { email: '' }) }
    setSending(true)
    try {
      await api('/auth/register/', { method: 'POST', body, auth: false })
      await login(mode === 'email' ? form.email.trim() : form.username.trim(), form.password)
      navigate(next)
    } catch (err) {
      const errs = fieldErrorsOf(err, FIELDS)
      // Email bilan ro'yxatdan o'tishda login xatosi aslida email haqida
      if (mode === 'email' && errs.username && !errs.email) errs.email = errs.username
      setErrors(errs)
      if (!Object.keys(errs).length) setError(errorText(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <form className="auth" onSubmit={submit} noValidate>
      <h1>{t("Ro'yxatdan o'tish")}</h1>
      <div className="form-row">
        <Field label={t('Ism')} required error={errors.first_name}>
          <input autoComplete="given-name" value={form.first_name} onChange={set('first_name')} className={errors.first_name ? 'invalid' : ''} />
        </Field>
        <Field label={t('Familiya')} required error={errors.last_name}>
          <input autoComplete="family-name" value={form.last_name} onChange={set('last_name')} className={errors.last_name ? 'invalid' : ''} />
        </Field>
      </div>
      <Field label={t('Telefon')} required error={errors.phone}>
        <input type="tel" inputMode="tel" autoComplete="tel" value={form.phone} onChange={set('phone')}
               placeholder="+998 90 123 45 67" className={errors.phone ? 'invalid' : ''} />
      </Field>

      <div className="seg">
        <button type="button" className={mode === 'email' ? 'on' : ''} onClick={() => setMode('email')}>{t('Email bilan')}</button>
        <button type="button" className={mode === 'login' ? 'on' : ''} onClick={() => setMode('login')}>{t('Login bilan')}</button>
      </div>
      {mode === 'email' ? (
        <Field label="Email" required error={errors.email}>
          <input type="email" autoComplete="email" value={form.email} onChange={set('email')} placeholder="name@mail.uz"
                 className={errors.email ? 'invalid' : ''} />
        </Field>
      ) : (
        <Field label={t('Login')} required error={errors.username}>
          <input autoComplete="username" value={form.username} onChange={set('username')} className={errors.username ? 'invalid' : ''} />
        </Field>
      )}
      <Field label={t('Parol')} required error={errors.password}>
        <input type="password" autoComplete="new-password" value={form.password} onChange={set('password')}
               className={errors.password ? 'invalid' : ''} />
      </Field>
      {error && <div className="error">{error}</div>}
      <button className="btn btn-lg" disabled={sending}>{sending ? t('Yuborilmoqda...') : t("Ro'yxatdan o'tish")}</button>
      <GoogleButton next={next} />
      <p className="muted">{t('Hisobingiz bormi?')} <Link to={`/login?next=${encodeURIComponent(next)}`}>{t('Kirish')}</Link></p>
    </form>
  )
}
