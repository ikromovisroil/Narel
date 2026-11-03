import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import ProductCard from '../components/ProductCard'

const SORTS = [
  ['-created_at', 'Avval yangilari'],
  ['price', 'Avval arzonlari'],
  ['-price', 'Avval qimmatlari'],
  ['name', 'Nomi bo\'yicha'],
]

export default function Catalog() {
  const { slug } = useParams()
  const [params, setParams] = useSearchParams()
  const [category, setCategory] = useState(null)
  const [brands, setBrands] = useState([])
  const [data, setData] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  const [price, setPrice] = useState({ min: params.get('price_min') || '', max: params.get('price_max') || '' })

  const selectedBrands = (params.get('brand') || '').split(',').filter(Boolean)
  const page = Number(params.get('page') || 1)

  useEffect(() => { api('/brands/', { auth: false }).then(setBrands).catch(() => {}) }, [])
  useEffect(() => {
    setCategory(null)
    if (slug) api(`/categories/${slug}/`, { auth: false }).then(setCategory).catch(() => {})
  }, [slug])

  useEffect(() => {
    const q = new URLSearchParams(params)
    if (slug) q.set('category', slug)
    if (!q.get('ordering')) q.set('ordering', '-created_at')
    setData(null)
    api(`/products/?${q}`, { auth: false }).then(setData).catch(() => setData({ results: [], count: 0 }))
  }, [slug, params])

  const update = changes => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes)) next.delete('page')
    setParams(next)
  }
  const toggleBrand = b => {
    const list = selectedBrands.includes(b) ? selectedBrands.filter(x => x !== b) : [...selectedBrands, b]
    update({ brand: list.join(',') })
  }

  const pages = data ? Math.ceil(data.count / 12) : 0
  const title = category?.name || (params.get('search') ? `"${params.get('search')}" bo'yicha qidiruv`
    : params.get('discount') ? 'Chegirmalar' : params.get('is_hit') ? 'Xit savdo'
    : params.get('is_new') ? 'Yangi mahsulotlar' : 'Barcha mahsulotlar')

  return (
    <div>
      <div className="crumbs">
        <Link to="/">Bosh sahifa</Link> › <Link to="/catalog">Katalog</Link>
        {category && <> › {category.name}</>}
      </div>
      <h1 className="page-title">{title} {data && <span className="muted">({data.count})</span>}</h1>

      <button className="btn btn-outline filters-toggle" onClick={() => setShowFilters(s => !s)}>
        {showFilters ? '✕ Filtrlarni yopish' : '⚙ Filtrlar'}
      </button>

      <div className="catalog">
        <aside className={`filters ${showFilters ? 'open' : ''}`}>
          {category?.children?.length > 0 && (
            <div className="filter-block">
              <h4>Kategoriyalar</h4>
              {category.children.map(c => <Link key={c.id} to={`/catalog/${c.slug}`}>{c.name}</Link>)}
            </div>
          )}
          <div className="filter-block">
            <h4>Narx, so'm</h4>
            <div className="price-inputs">
              <input type="number" placeholder="dan" value={price.min}
                     onChange={e => setPrice({ ...price, min: e.target.value })} />
              <input type="number" placeholder="gacha" value={price.max}
                     onChange={e => setPrice({ ...price, max: e.target.value })} />
            </div>
            <button className="btn btn-sm" onClick={() => update({ price_min: price.min, price_max: price.max })}>
              Qo'llash
            </button>
          </div>
          <div className="filter-block">
            <h4>Brend</h4>
            {brands.map(b => (
              <label key={b.id} className="check">
                <input type="checkbox" checked={selectedBrands.includes(b.slug)} onChange={() => toggleBrand(b.slug)} />
                {b.name}
              </label>
            ))}
          </div>
          <div className="filter-block">
            <label className="check">
              <input type="checkbox" checked={params.get('discount') === 'true'}
                     onChange={e => update({ discount: e.target.checked ? 'true' : '' })} />
              Faqat chegirmadagilar
            </label>
          </div>
        </aside>

        <div className="catalog-main">
          <div className="sortbar">
            {SORTS.map(([v, label]) => (
              <button key={v} className={(params.get('ordering') || '-created_at') === v ? 'on' : ''}
                      onClick={() => update({ ordering: v })}>{label}</button>
            ))}
          </div>

          {!data ? <div className="muted">Yuklanmoqda...</div>
            : !data.results.length ? <div className="empty">Hech narsa topilmadi</div>
            : <div className="grid">{data.results.map(p => <ProductCard key={p.id} p={p} />)}</div>}

          {pages > 1 && (
            <div className="pager">
              {Array.from({ length: pages }, (_, i) => i + 1).map(n => (
                <button key={n} className={n === page ? 'on' : ''}
                        onClick={() => { update({ page: n === 1 ? '' : String(n) }); window.scrollTo(0, 0) }}>
                  {n}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
