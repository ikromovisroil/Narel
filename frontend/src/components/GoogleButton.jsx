import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorText } from '../api'
import { t } from '../i18n'
import { useStore } from '../store'

const SCRIPT = 'https://accounts.google.com/gsi/client'
let loading = null
// Google Identity Services skriptini bir marta yuklaydi
function loadGoogle() {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = SCRIPT
      s.async = true
      s.onload = resolve
      s.onerror = () => { loading = null; reject(new Error('google')) }
      document.head.appendChild(s)
    })
  }
  return loading
}

// "Google bilan davom etish" tugmasi. Admin .env da GOOGLE_CLIENT_ID qo'ymagan bo'lsa ko'rinmaydi.
export default function GoogleButton({ next = '/' }) {
  const { storeInfo, googleLogin, lang } = useStore()
  const clientId = storeInfo?.google_client_id
  const box = useRef(null)
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    if (!clientId) return
    let alive = true
    loadGoogle().then(() => {
      if (!alive || !box.current) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async ({ credential }) => {
          setError('')
          try {
            const r = await googleLogin(credential)
            // Yangi hisob — telefon va manzilni to'ldirish uchun profilga
            navigate(r.created ? `/profile?next=${encodeURIComponent(next)}` : next)
          } catch (err) {
            setError(errorText(err))
          }
        },
      })
      box.current.innerHTML = ''
      window.google.accounts.id.renderButton(box.current, {
        theme: 'outline', size: 'large', text: 'continue_with', shape: 'rectangular',
        width: Math.min(box.current.offsetWidth || 360, 400), locale: lang === 'ru' ? 'ru' : 'uz',
      })
    }).catch(() => alive && setError(t("Google xizmatiga ulanib bo'lmadi.")))
    return () => { alive = false }
  }, [clientId, lang, googleLogin, navigate, next])

  if (!clientId) return null
  return (
    <>
      <div ref={box} className="google-btn" />
      {error && <div className="error">{error}</div>}
    </>
  )
}

// "yoki" chizig'i — Google yoqilgan bo'lsa
export function SocialDivider() {
  const { storeInfo } = useStore()
  if (!storeInfo?.google_client_id) return null
  return <div className="or-line"><span>{t('yoki')}</span></div>
}
