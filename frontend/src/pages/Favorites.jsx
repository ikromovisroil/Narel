import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { useStore } from '../store'

export default function Favorites() {
  const { favorites } = useStore()
  return (
    <div>
      <h1 className="page-title">Saralanganlar</h1>
      {favorites.length
        ? <div className="grid">{favorites.map(p => <ProductCard key={p.id} p={p} />)}</div>
        : <div className="empty">Saralangan mahsulotlar yo'q. <Link to="/catalog">Katalogga o'tish</Link></div>}
    </div>
  )
}
