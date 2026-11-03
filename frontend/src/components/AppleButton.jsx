import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorText } from '../api'
import { t } from '../i18n'
import { useStore } from '../store'

const SCRIPT = 'https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js'
let loading = null
function loadApple() {
  if (window.AppleID) return Promise.resolve()
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = SCRIPT
      s.async = true
      s.onload = resolve
      s.onerror = () => { loading = null; reject(new Error('apple')) }
      document.head.appendChild(s)
    })
  }
  return loading
}

const AppleLogo = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
    <path d="M16.37 12.6c-.02-2.3 1.88-3.4 1.96-3.46-1.07-1.56-2.73-1.78-3.32-1.8-1.41-.14-2.76.83-3.48.83-.72 0-1.82-.81-3-.79-1.54.02-2.96.9-3.76 2.28-1.6 2.78-.41 6.9 1.15 9.16.76 1.1 1.67 2.34 2.86 2.3 1.15-.05 1.58-.74 2.97-.74 1.38 0 1.77.74 2.98.72 1.23-.02 2.01-1.12 2.76-2.23.87-1.28 1.23-2.52 1.25-2.58-.03-.01-2.39-.92-2.41-3.64zM14.1 5.84c.63-.77 1.06-1.83.94-2.89-.91.04-2.01.61-2.66 1.37-.58.67-1.09 1.76-.96 2.8 1.02.08 2.05-.52 2.68-1.28z" />
  </svg>
)

// "Apple orqali kirish". .env da APPLE_CLIENT_ID bo'lmasa ko'rinmaydi.
export default function AppleButton({ next = '/' }) {
  const { storeInfo, tokenLogin } = useStore()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const clientId = storeInfo?.apple_client_id
  if (!clientId) return null

  const click = async () => {
    setError('')
    setBusy(true)
    try {
      await loadApple()
      window.AppleID.auth.init({
        clientId, scope: 'name email', redirectURI: `${window.location.origin}/login`, usePopup: true,
      })
      const res = await window.AppleID.auth.signIn()
      const name = res.user?.name || {}
      const r = await tokenLogin('/auth/apple/', {
        id_token: res.authorization.id_token, first_name: name.firstName || '', last_name: name.lastName || '',
      })
      navigate(r.created ? `/profile?next=${encodeURIComponent(next)}` : next)
    } catch (err) {
      // Foydalanuvchi oynani yopsa — xato ko'rsatmaymiz
      if (err?.error !== 'popup_closed_by_user') setError(err?.status ? errorText(err) : t("Apple orqali kirib bo'lmadi."))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button type="button" className="social-btn" onClick={click} disabled={busy}>
        <AppleLogo /> {t('Apple orqali kirish')}
      </button>
      {error && <div className="error">{error}</div>}
    </>
  )
}
