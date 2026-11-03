import { useEffect, useState } from 'react'
import { api } from '../api'
import { t } from '../i18n'
import ProductCard from './ProductCard'

// Mahsulot sahifasi ostida: shu kategoriyadagi o'xshash mahsulotlar
export default function SimilarProducts({ slug }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    setItems([])
    api(`/products/${slug}/similar/`, { auth: false }).then(setItems).catch(() => setItems([]))
  }, [slug])

  if (!items.length) return null
  return (
    <section className="section">
      <div className="section-head"><h2>{t("O'xshash mahsulotlar")}</h2></div>
      <div className="grid grid-scroll">
        {items.map(p => <ProductCard key={p.id} p={p} />)}
      </div>
    </section>
  )
}
