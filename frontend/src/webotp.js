import { useEffect, useRef } from 'react'

// Android Chrome: SMS kelganda kodni o'zi oladi (WebOTP). SMS oxirida "@domen #kod" qatori bo'lishi kerak —
// admin panel → Sozlamalar → Integratsiyalar → SMS → "Kodni avtomatik to'ldirish".
// iPhone'da bu kerak emas: autoComplete="one-time-code" orqali klaviatura ustida taklif chiqadi.
export function useWebOtp(active, onCode) {
  const callback = useRef(onCode)
  callback.current = onCode

  useEffect(() => {
    if (!active || typeof window === 'undefined' || !('OTPCredential' in window)) return undefined
    const ac = new AbortController()
    navigator.credentials
      .get({ otp: { transport: ['sms'] }, signal: ac.signal })
      .then(otp => { if (otp?.code) callback.current(otp.code.replace(/\D/g, '').slice(0, 6)) })
      .catch(() => {}) // bekor qilindi yoki ruxsat berilmadi — qo'lda kiritiladi
    return () => ac.abort()
  }, [active])
}
