import { Link } from 'react-router-dom'
import { SHOP_NAME } from '../api'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <div className="logo">{SHOP_NAME}</div>
          <p className="muted">Elektronika va maishiy texnika. Rasmiy kafolat, tez yetkazib berish, muddatli to'lov.</p>
        </div>
        <div>
          <h4>Xaridorlarga</h4>
          <Link to="/catalog">Katalog</Link>
          <Link to="/catalog?discount=true">Chegirmalar</Link>
          <Link to="/orders">Buyurtmalarim</Link>
        </div>
        <div>
          <h4>Bog'lanish</h4>
          <span>+998 71 000 00 00</span>
          <span>info@techshop.uz</span>
          <span className="muted">Toshkent sh.</span>
        </div>
      </div>
      <div className="container copyright muted">© {new Date().getFullYear()} {SHOP_NAME}</div>
    </footer>
  )
}
