import { Link } from 'react-router-dom'
import { SHOP_NAME } from '../api'
import { t } from '../i18n'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <div className="logo">{SHOP_NAME}</div>
          <p className="muted">{t("Elektronika va maishiy texnika. Rasmiy kafolat, tez yetkazib berish, muddatli to'lov.")}</p>
        </div>
        <div>
          <h4>{t('Xaridorlarga')}</h4>
          <Link to="/catalog">{t('Katalog')}</Link>
          <Link to="/catalog?discount=true">{t('Chegirmalar')}</Link>
          <Link to="/orders">{t('Buyurtmalarim')}</Link>
        </div>
        <div>
          <h4>{t("Bog'lanish")}</h4>
          <span>+998 71 000 00 00</span>
          <span>info@techshop.uz</span>
          <span className="muted">{t('Toshkent sh.')}</span>
        </div>
      </div>
      <div className="container copyright muted">© 2026 {SHOP_NAME}</div>
    </footer>
  )
}
