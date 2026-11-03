import { useEffect, useState } from 'react'
import { App, Button, Image, Input, Popconfirm, Select, Space, Switch, Table, Tag, Typography } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { formatPrice } from '../utils'
import { useCanEdit, usePerm } from '../auth'

export default function Products() {
  const canEdit = useCanEdit('products')
  const perm = usePerm('products')
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState([])
  const [brands, setBrands] = useState([])
  const [search, setSearch] = useState(params.get('search') || '')
  const [reload, setReload] = useState(0)

  const filters = Object.fromEntries(params)
  const page = Number(filters.page || 1)

  useEffect(() => {
    api('/admin/categories/').then(setCategories)
    api('/admin/brands/').then(setBrands)
  }, [])

  useEffect(() => {
    setLoading(true)
    api(`/admin/products/?${params}`).then(setData).finally(() => setLoading(false))
  }, [params, reload])

  const update = changes => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v !== undefined && v !== null && v !== '' ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes)) next.delete('page')
    setParams(next)
  }

  const patch = async (id, body) => {
    try {
      const p = await api(`/admin/products/${id}/`, { method: 'PATCH', body })
      setData(d => ({ ...d, results: d.results.map(x => (x.id === id ? p : x)) }))
    } catch (err) {
      message.error(errorText(err))
    }
  }

  const remove = async id => {
    try {
      await api(`/admin/products/${id}/`, { method: 'DELETE' })
      message.success('O\'chirildi')
      setReload(r => r + 1)
    } catch (err) {
      message.error(errorText(err))
    }
  }

  const ordering = filters.ordering || ''
  const sortOrder = key => (ordering === key ? 'ascend' : ordering === `-${key}` ? 'descend' : null)

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Mahsulotlar</Typography.Title>
        {perm.add && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/products/new')}>
            Mahsulot qo'shish
          </Button>
        )}
      </div>

      <div className="toolbar">
        <Input.Search placeholder="Nomi, mahsulot kodi, brend" allowClear value={search} style={{ width: 240 }}
                      onChange={e => setSearch(e.target.value)} onSearch={v => update({ search: v })} />
        <Select placeholder="Kategoriya" allowClear showSearch optionFilterProp="label" style={{ width: 200 }}
                value={filters.category ? Number(filters.category) : undefined}
                options={categories.map(c => ({ value: c.id, label: c.name }))}
                onChange={v => update({ category: v })} />
        <Select placeholder="Brend" allowClear showSearch optionFilterProp="label" style={{ width: 160 }}
                value={filters.brand ? Number(filters.brand) : undefined}
                options={brands.map(b => ({ value: b.id, label: b.name }))}
                onChange={v => update({ brand: v })} />
        <Select placeholder="Holati" allowClear style={{ width: 150 }} value={filters.is_active}
                options={[{ value: 'true', label: 'Faol' }, { value: 'false', label: 'Yashirin' }]}
                onChange={v => update({ is_active: v })} />
        <Button type={filters.low_stock ? 'primary' : 'default'} danger={Boolean(filters.low_stock)}
                onClick={() => update({ low_stock: filters.low_stock ? '' : 'true' })}>
          Kam qolganlar
        </Button>
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={data.results} scroll={{ x: 1100 }}
        onChange={(_, __, sorter) => update({
          ordering: sorter.order ? `${sorter.order === 'descend' ? '-' : ''}${sorter.field}` : '',
        })}
        pagination={{
          current: page, total: data.count, pageSize: 20, showSizeChanger: false,
          showTotal: t => `Jami: ${t}`, onChange: p => update({ page: p === 1 ? '' : String(p) }),
        }}
        columns={[
          {
            title: '', dataIndex: 'image', width: 64,
            render: src => (src ? <Image src={src} width={44} height={44} style={{ objectFit: 'contain' }} />
              : <div className="thumb">📦</div>),
          },
          {
            title: 'Nomi', dataIndex: 'name', sorter: true, sortOrder: sortOrder('name'),
            render: (name, p) => (
              <Space orientation="vertical" size={0}>
                <Link to={`/products/${p.id}`}>{name}</Link>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {p.category_name}{p.brand_name && ` · ${p.brand_name}`}{p.sku && ` · ${p.sku}`}
                </Typography.Text>
              </Space>
            ),
          },
          {
            title: 'Narx', dataIndex: 'price', sorter: true, sortOrder: sortOrder('price'), align: 'right',
            render: (price, p) => (
              <Space orientation="vertical" size={0} style={{ alignItems: 'flex-end' }}>
                <b>{formatPrice(price)}</b>
                {p.old_price && <Typography.Text delete type="secondary" style={{ fontSize: 12 }}>{formatPrice(p.old_price)}</Typography.Text>}
              </Space>
            ),
          },
          {
            title: 'Omborda', dataIndex: 'stock', sorter: true, sortOrder: sortOrder('stock'), align: 'center',
            render: s => <Tag color={s === 0 ? 'red' : s <= 5 ? 'orange' : 'green'}>{s}</Tag>,
          },
          { title: 'Sotilgan', dataIndex: 'sold', sorter: true, sortOrder: sortOrder('sold'), align: 'center' },
          {
            title: 'Belgilar', key: 'flags',
            render: (_, p) => (
              <Space size={4} wrap>
                {p.is_hit && <Tag color="orange">Xit</Tag>}
                {p.is_new && <Tag color="green">Yangi</Tag>}
                {p.old_price && <Tag color="red">Chegirma</Tag>}
              </Space>
            ),
          },
          {
            title: 'Faol', dataIndex: 'is_active', align: 'center',
            render: (v, p) => <Switch size="small" checked={v} disabled={!canEdit} onChange={c => patch(p.id, { is_active: c })} />,
          },
          {
            title: '', key: 'actions', width: 100, fixed: 'right',
            render: (_, p) => (
              <Space>
                <Button icon={<EditOutlined />} onClick={() => navigate(`/products/${p.id}`)} />
                {perm.delete && (
                  <Popconfirm title="Mahsulotni o'chirasizmi?" okText="Ha" cancelText="Yo'q"
                              okButtonProps={{ danger: true }} onConfirm={() => remove(p.id)}>
                    <Button danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />
    </>
  )
}
