import { Link } from 'react-router-dom'
import { SHOP_NAME } from '../api'
import Logo from './Logo'
import { t } from '../i18n'
import { useStore } from '../store'

export default function Footer() {
  const { storeInfo } = useStore()
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <Logo dark link={false} />
          <p className="muted">{t("Elektronika va maishiy texnika. Rasmiy kafolat, tez yetkazib berish, muddatli to'lov.")}</p>
        </div>
        <div>
          <h4>{t('Xaridorlarga')}</h4>
          <Link to="/catalog">{t('Katalog')}</Link>
          <Link to="/catalog?discount=true">{t('Chegirmalar')}</Link>
          <Link to="/orders">{t('Buyurtmalarim')}</Link>
          <Link to="/oferta">{t('Ommaviy oferta')}</Link>
        </div>
        <div>
          <h4>{t("Bog'lanish")}</h4>
          {storeInfo && <a href={`tel:${storeInfo.phone.replace(/[^\d+]/g, '')}`}>{storeInfo.phone}</a>}
          <span>info@narel.uz</span>
          {storeInfo && <span className="muted">{storeInfo.address}</span>}
          {storeInfo?.working_hours && <span className="muted">{storeInfo.working_hours}</span>}
        </div>
      </div>
      <div className="container copyright muted">
        <span>© 2026 {SHOP_NAME}</span>
        <a className="dev-credit" href="https://t.me/Isroil_0309" target="_blank" rel="noopener noreferrer">
          {t('Dasturchi')}: Ikromov.I
        </a>
      </div>
    </footer>
  )
}
