import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { t } from '../i18n'
import { useStore } from '../store'

function useNext() {
  const [params] = useSearchParams()
  const next = params.get('next') || '/'
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
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
      <label>{t('Login')}<input required autoComplete="username" value={form.username}
                         onChange={e => setForm({ ...form, username: e.target.value })} /></label>
      <label>{t('Parol')}<input required type="password" autoComplete="current-password" value={form.password}
                         onChange={e => setForm({ ...form, password: e.target.value })} /></label>
      {error && <div className="error">{error}</div>}
      <button className="btn btn-lg">{t('Kirish')}</button>
      <p className="muted">{t("Hisobingiz yo'qmi?")} <Link to={`/register?next=${encodeURIComponent(next)}`}>{t("Ro'yxatdan o'tish")}</Link></p>
    </form>
  )
}

export function Register() {
  const { login } = useStore()
  const navigate = useNavigate()
  const next = useNext()
  const [form, setForm] = useState({ username: '', first_name: '', last_name: '', email: '', password: '' })
  const [error, setError] = useState('')

  const set = k => e => setForm({ ...form, [k]: e.target.value })
  const submit = async e => {
    e.preventDefault()
    setError('')
    try {
      await api('/auth/register/', { method: 'POST', body: form, auth: false })
      await login(form.username, form.password)
      navigate(next)
    } catch (err) {
      setError(errorText(err))
    }
  }

  return (
    <form className="auth" onSubmit={submit}>
      <h1>{t("Ro'yxatdan o'tish")}</h1>
      <div className="form-row">
        <label>{t('Ism')}<input value={form.first_name} onChange={set('first_name')} /></label>
        <label>{t('Familiya')}<input value={form.last_name} onChange={set('last_name')} /></label>
      </div>
      <label>{t('Login')}<input required autoComplete="username" value={form.username} onChange={set('username')} /></label>
      <label>Email<input type="email" value={form.email} onChange={set('email')} /></label>
      <label>{t('Parol')}<input required type="password" autoComplete="new-password" value={form.password}
                         onChange={set('password')} /></label>
      {error && <div className="error">{error}</div>}
      <button className="btn btn-lg">{t("Ro'yxatdan o'tish")}</button>
      <p className="muted">{t('Hisobingiz bormi?')} <Link to={`/login?next=${encodeURIComponent(next)}`}>{t('Kirish')}</Link></p>
    </form>
  )
}
