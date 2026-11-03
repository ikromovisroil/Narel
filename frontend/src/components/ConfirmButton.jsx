import { useEffect, useState } from 'react'
import { t } from '../i18n'

// Tugma + saytning o'z tasdiqlash oynasi.
// window.confirm ishlatilmaydi: ba'zi brauzerlar (ilova ichidagi) uni bloklaydi va tugma ishlamay qoladi.
export default function ConfirmButton({ className, children, title, text, okLabel, onConfirm }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return undefined
    const onKey = e => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  const confirm = async () => {
    setBusy(true)
    try {
      await onConfirm()
      setOpen(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button type="button" className={className} onClick={() => setOpen(true)}>{children}</button>
      {open && (
        <div className="confirm-overlay" onClick={() => setOpen(false)}>
          <div className="confirm-box" role="dialog" aria-modal="true" onClick={e => e.stopPropagation()}>
            <b className="confirm-title">{title}</b>
            {text && <p className="muted">{text}</p>}
            <div className="confirm-actions">
              <button type="button" className="btn btn-outline btn-sm" onClick={() => setOpen(false)} autoFocus>
                {t("Yo'q")}
              </button>
              <button type="button" className="btn btn-sm btn-danger" disabled={busy} onClick={confirm}>
                {okLabel || t('Ha')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
