import { useId } from 'react'
import { Link } from 'react-router-dom'
import { SHOP_NAME } from '../api'

// Rendershop belgisi: gradientli xarid sumkasi ichida kub (public/favicon.svg bilan bir xil)
export function LogoMark({ size = 36 }) {
  const id = useId()
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id={id} x1="10" y1="21" x2="55" y2="61" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#5b6cf2" />
          <stop offset="1" stopColor="#12b3d6" />
        </linearGradient>
      </defs>
      <path d="M23 24 V17 a9 9 0 0 1 18 0 V24" stroke="#4f74e8" strokeWidth="4.5" strokeLinecap="round" />
      <path d="M13 21 H51 a3 3 0 0 1 3 3 L55.5 55 a5 5 0 0 1 -5 5.5 H13.5 a5 5 0 0 1 -5 -5.5 L10 24 a3 3 0 0 1 3 -3 Z" fill={`url(#${id})`} />
      <path d="M32 30 L40.5 34.8 V44.6 L32 49.4 L23.5 44.6 V34.8 Z M23.5 34.8 L32 39.6 L40.5 34.8 M32 39.6 V49.4"
        stroke="#fff" strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

export default function Logo({ dark = false, link = true }) {
  const content = (
    <>
      <LogoMark />
      <span className="logo-text">
        <span className="logo-text-1">Render</span><span className="logo-text-2">shop</span>
      </span>
    </>
  )
  return link
    ? <Link to="/" className={`logo ${dark ? 'logo-dark' : ''}`} aria-label={SHOP_NAME}>{content}</Link>
    : <div className={`logo ${dark ? 'logo-dark' : ''}`}>{content}</div>
}
