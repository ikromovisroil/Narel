import { useEffect, useRef, useState } from 'react'
import { api, errorText } from '../api'
import { t } from '../i18n'
import { formatPhone, phoneOk } from '../phone'
import { useStore } from '../store'

const firstError = (err, key) => [].concat(err?.data?.[key] || [])[0]

// Telefonni SMS kod bilan tasdiqlash: profilda almashtirish yoki Google/Apple mijozida qo'shish
export default function PhoneVerify({ onDone, onCancel }) {
  const { user, setUser } = useStore()
  const [phone, setPhone] = useState('+998 ')
  const [step, setStep] = useState('phone')
  const [code, setCode] = useState('')
  const [debug, setDebug] = useState('')
  const [left, setLeft] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const codeRef = useRef(null)

  useEffect(() => {
    if (left <= 0) return undefined
    const id = setTimeout(() => setLeft(l => l - 1), 1000)
    return () => clearTimeout(id)
  }, [left])

  const send = async () => {
    setError('')
    if (!phoneOk(phone)) return setError(t("Telefon raqamini to'liq kiriting: +998 XX XXX XX XX."))
    setBusy(true)
    try {
      const r = await api('/auth/code/send/', { method: 'POST', body: { phone, agree: true } })
      setDebug(r.debug_code || '')
      setStep('code')
      setCode('')
      setLeft(r.resend_in)
      setTimeout(() => codeRef.current?.focus(), 50)
    } catch (err) {
      if (err?.data?.resend_in) { setStep('code'); setLeft(err.data.resend_in) }
      setError(firstError(err, 'phone') || errorText(err))
    } finally {
      setBusy(false)
    }
  }

  const verify = async value => {
    setError('')
    setBusy(true)
    try {
      const r = await api('/auth/phone/', { method: 'POST', body: { phone, code: value } })
      setUser({ ...user, phone: r.phone })
      onDone?.(r.phone)
    } catch (err) {
      setError(firstError(err, 'phone') || firstError(err, 'code') || errorText(err))
      setCode('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="phone-verify">
      {step === 'phone' ? (
        <div className="pv-row">
          <input type="tel" inputMode="tel" autoComplete="tel" value={phone} placeholder="+998 90 123 45 67" autoFocus
                 onChange={e => { setPhone(formatPhone(e.target.value)); setError('') }}
                 onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); send() } }} />
          <button type="button" className="btn" onClick={send} disabled={busy || !phoneOk(phone)}>
            {busy ? t('Yuborilmoqda...') : t('Kodni yuborish')}
          </button>
        </div>
      ) : (
        <>
          <span className="muted small">
            {t('Kod {phone} raqamiga yuborildi.', { phone })}{' '}
            <button type="button" className="link" onClick={() => { setStep('phone'); setError('') }}>{t("Raqamni o'zgartirish")}</button>
          </span>
          {debug && <div className="notice small">{t('Test rejimi (SMS yuborilmaydi): kod — {code}', { code: debug })}</div>}
          <div className="pv-row">
            <input ref={codeRef} className="code-input" inputMode="numeric" autoComplete="one-time-code" placeholder="••••••"
                   value={code} disabled={busy}
                   onChange={e => { const v = e.target.value.replace(/\D/g, '').slice(0, 6); setCode(v); if (v.length === 6) verify(v) }} />
          </div>
          {left > 0
            ? <span className="muted small">{t('Kodni qayta yuborish: {s} soniya', { s: left })}</span>
            : <button type="button" className="link small" onClick={send} disabled={busy}>{t('Kodni qayta yuborish')}</button>}
        </>
      )}
      {error && <span className="field-error">{error}</span>}
      {onCancel && <button type="button" className="link small" onClick={onCancel}>{t('Bekor qilish')}</button>}
    </div>
  )
}
