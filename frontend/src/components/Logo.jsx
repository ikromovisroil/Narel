import { Link } from 'react-router-dom'
import { SHOP_NAME } from '../api'

// Narel belgisi: monitor ichida "N". dark — to'q fon (footer) uchun yorug' variant
export function LogoMark({ size = 36, dark = false }) {
  const body = dark ? '#ffffff' : '#0f1b2d'
  const letter = dark ? '#0f1b2d' : '#ffffff'
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <rect x="5" y="7" width="54" height="40" rx="10" fill={body} />
      <rect x="29.5" y="46" width="5" height="8" fill={body} />
      <path d="M22 18 L42 36" stroke="#2f6bff" strokeWidth="5.5" strokeLinecap="round" />
      <path d="M22 18 V36 M42 18 V36" stroke={letter} strokeWidth="5.5" strokeLinecap="round" />
      <path d="M20.5 55.5 H43.5" stroke="#2f6bff" strokeWidth="5.5" strokeLinecap="round" />
    </svg>
  )
}

export default function Logo({ dark = false, link = true }) {
  const content = (
    <>
      <LogoMark dark={dark} />
      <span className="logo-text">{SHOP_NAME}</span>
    </>
  )
  return link
    ? <Link to="/" className={`logo ${dark ? 'logo-dark' : ''}`} aria-label={SHOP_NAME}>{content}</Link>
    : <div className={`logo ${dark ? 'logo-dark' : ''}`}>{content}</div>
}
