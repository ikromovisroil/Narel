import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorText, tokens } from '../api'
import GoogleButton, { SocialDivider } from '../components/GoogleButton'
import { t } from '../i18n'
import { formatPhone, phoneOk } from '../phone'
import { useStore } from '../store'
import { useNext } from './Auth'
import { useWebOtp } from '../webotp'

const firstError = (err, key) => [].concat(err?.data?.[key] || [])[0]

// Qayta yuborishgacha qolgan soniyalar
function useCountdown() {
  const [left, setLeft] = useState(0)
  useEffect(() => {
    if (left <= 0) return undefined
    const id = setTimeout(() => setLeft(l => l - 1), 1000)
    return () => clearTimeout(id)
  }, [left])
  return [left, setLeft]
}

// Telefon + SMS kod: raqam yangi bo'lsa hisob o'zi ochiladi
function PhoneLogin({ next }) {
  const { tokenLogin, storeInfo } = useStore()
  const navigate = useNavigate()
  const [step, setStep] = useState('phone') // phone | code
  const [phone, setPhone] = useState('+998 ')
  const [agree, setAgree] = useState(false)
  const [code, setCode] = useState('')
  const [sent, setSent] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [left, setLeft] = useCountdown()
  const codeRef = useRef(null)

  const send = async e => {
    e?.preventDefault()
    setError('')
    if (!phoneOk(phone)) return setError(t("Telefon raqamini to'liq kiriting: +998 XX XXX XX XX."))
    if (!agree) return setError(t('Shartlarga rozilikni tasdiqlang.'))
    setBusy(true)
    try {
      const r = await api('/auth/code/send/', { method: 'POST', body: { phone, agree }, auth: false })
      setSent(r)
      setStep('code')
      setCode('')
      setLeft(r.resend_in)
      setTimeout(() => codeRef.current?.focus(), 50)
    } catch (err) {
      if (err?.data?.resend_in) { setStep('code'); setLeft(err.data.resend_in) }
      setError(firstError(err, 'phone') || firstError(err, 'agree') || errorText(err))
    } finally {
      setBusy(false)
    }
  }

  const verify = async value => {
    setError('')
    setBusy(true)
    try {
      const r = await tokenLogin('/auth/code/verify/', { phone, code: value })
      // Yangi mijoz — ism va manzilni to'ldirish uchun profilga
      navigate(r.created ? `/profile?next=${encodeURIComponent(next)}` : next)
    } catch (err) {
      setError(firstError(err, 'code') || errorText(err))
      setCode('')
      codeRef.current?.focus()
    } finally {
      setBusy(false)
    }
  }

  const onCode = e => {
    const v = e.target.value.replace(/\D/g, '').slice(0, 6)
    setCode(v)
    if (v.length === 6) verify(v)
  }

  // Android: SMS kelganda kod o'zi tushadi va kirish boshlanadi
  useWebOtp(step === 'code' && !busy, c => { setCode(c); if (c.length === 6) verify(c) })

  if (step === 'code') {
    return (
      <form className="login-form" onSubmit={e => { e.preventDefault(); if (code.length === 6) verify(code) }}>
        <p className="login-sub">
          {t('Kod {phone} raqamiga yuborildi.', { phone: sent?.phone || phone })}{' '}
          <button type="button" className="link" onClick={() => { setStep('phone'); setError('') }}>{t("Raqamni o'zgartirish")}</button>
        </p>
        {sent?.debug_code && (
          <div className="notice small">{t('Test rejimi (SMS yuborilmaydi): kod — {code}', { code: sent.debug_code })}</div>
        )}
        <label>
          <span>{t('SMS kod')}</span>
          <input ref={codeRef} className={`code-input ${error ? 'invalid' : ''}`} inputMode="numeric" autoComplete="one-time-code"
                 placeholder="••••••" value={code} onChange={onCode} disabled={busy} />
        </label>
        {error && <div className="field-error">{error}</div>}
        <button className="btn btn-lg" disabled={busy || code.length !== 6}>{busy ? t('Tekshirilmoqda...') : t('Kirish')}</button>
        <div className="resend">
          {left > 0
            ? <span className="muted small">{t('Kodni qayta yuborish: {s} soniya', { s: left })}</span>
            : <button type="button" className="link" onClick={send} disabled={busy}>{t('Kodni qayta yuborish')}</button>}
        </div>
      </form>
    )
  }

  return (
    <form className="login-form" onSubmit={send} noValidate>
      <label>
        <span>{t('Telefon')} <span className="req">*</span></span>
        <input type="tel" inputMode="tel" autoComplete="tel" value={phone} autoFocus
               onChange={e => { setPhone(formatPhone(e.target.value)); setError('') }} placeholder="+998 90 123 45 67" />
      </label>
      <label className="agree">
        <input type="checkbox" checked={agree} onChange={e => { setAgree(e.target.checked); setError('') }} />
        <span>
          {t('Shartlar bilan tanishganligimni va ularga roziligimni tasdiqlayman.')}{' '}
          <Link to="/oferta" target="_blank">{t('Ommaviy oferta')}</Link>
        </span>
      </label>
      {error && <div className="field-error">{error}</div>}
      {storeInfo?.sms_test_mode && <div className="muted small">{t('Test rejimi: kod SMS o‘rniga ekranda ko‘rsatiladi.')}</div>}
      <button className="btn btn-lg" disabled={busy || !agree || !phoneOk(phone)}>
        {busy ? t('Yuborilmoqda...') : t('Kodni yuborish')}
      </button>
    </form>
  )
}

// Kirish yoki ro'yxatdan o'tish oynasi
export default function Login() {
  const navigate = useNavigate()
  const next = useNext()
  // Allaqachon kirgan bo'lsa — darhol qaytaramiz (kirish jarayonidagi yo'naltirishga xalaqit bermaydi)
  useEffect(() => { if (tokens.access) navigate(next, { replace: true }) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="login-wrap">
      <div className="login-card">
        <button className="login-close" aria-label={t('Yopish')} onClick={() => navigate(-1)}>×</button>
        <h1>{t("Kirish yoki ro'yxatdan o'tish")}</h1>
        <PhoneLogin next={next} />
        <SocialDivider />
        <GoogleButton next={next} />
      </div>
    </div>
  )
}
