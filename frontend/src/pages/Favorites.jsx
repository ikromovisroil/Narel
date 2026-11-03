import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import ConfirmButton from '../components/ConfirmButton'
import { HeartIcon, TrashIcon } from '../components/Icons'
import ProductCard from '../components/ProductCard'
import { t } from '../i18n'
import { useStore } from '../store'

export default function Favorites() {
  const { favorites, clearFavorites, refreshFavorites } = useStore()

  // Narx va ombordagi son o'zgargan bo'lishi mumkin — sahifa ochilganda yangilaymiz
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (favorites.length) refreshFavorites() }, [])

  if (!favorites.length) {
    return (
      <div className="empty">
        <div className="empty-icon"><HeartIcon size={44} /></div>
        <h2>{t("Sevimlilar ro'yxati bo'sh")}</h2>
        <p className="muted">{t("Yoqqan mahsulotlarni yurakcha belgisi orqali shu yerga qo'shing")}</p>
        <Link className="btn" to="/catalog">{t("Katalogga o'tish")}</Link>
      </div>
    )
  }

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">{t('Sevimlilar')} <span className="muted">({favorites.length})</span></h1>
        <ConfirmButton className="clear-btn" title={t("Sevimlilar ro'yxatini tozalaysizmi?")}
                       okLabel={t('Tozalash')} onConfirm={clearFavorites}>
          <TrashIcon size={16} /> {t('Tozalash')}
        </ConfirmButton>
      </div>
      <div className="grid">{favorites.map(p => <ProductCard key={p.id} p={p} />)}</div>
    </div>
  )
}
