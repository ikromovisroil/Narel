import { t } from '../i18n'
import { useStore } from '../store'

// Olib ketish joyi qisqacha: bitta filial bo'lsa manzili, ko'p bo'lsa soni
export function pickupWhere(info) {
  const list = info?.branches || []
  return list.length > 1 ? t('{n} ta filial', { n: list.length }) : list[0]?.address || info?.address || ''
}

// Manzil, telefon va ish vaqti: filial (info) yoki do'konning asosiy aloqasi
export default function StoreInfo({ title, info }) {
  const { storeInfo } = useStore()
  const s = info || storeInfo
  if (!s) return null
  return (
    <div className="store-info">
      {title && <b className="store-info-title">{title}</b>}
      {info?.name && info.address && <b>{info.name}</b>}
      <div>📍 {s.address || s.name}{s.map_url && <> · <a href={s.map_url} target="_blank" rel="noreferrer">{t("Xaritada ko'rish")}</a></>}</div>
      {s.phone && <div>☎ <a href={`tel:${s.phone.replace(/[^\d+]/g, '')}`}>{s.phone}</a></div>}
      {s.working_hours && <div>🕘 {s.working_hours}</div>}
    </div>
  )
}
