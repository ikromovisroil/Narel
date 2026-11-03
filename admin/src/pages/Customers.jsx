import { useEffect, useState } from 'react'
import { Drawer, Input, Table, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { scrollToTable, formatPrice, ORDER_STATUS } from '../utils'

function CustomerOrders({ customer, onClose }) {
  const [orders, setOrders] = useState(null)
  useEffect(() => {
    setOrders(null)
    if (customer) api('/admin/orders/', { params: { user: customer.id, page_size: 100 } }).then(r => setOrders(r.results))
  }, [customer])

  return (
    <Drawer open={Boolean(customer)} onClose={onClose} size={560}
            title={customer && (`${customer.first_name} ${customer.last_name}`.trim() || customer.phone || 'Mijoz')}>
      {customer && (
        <>
          <Typography.Paragraph type="secondary">
            {[customer.phone, customer.email].filter(Boolean).join(' · ') || '—'}<br />
            Ro'yxatdan o'tgan: {dayjs(customer.date_joined).format('DD.MM.YYYY')}<br />
            Jami xarid: <b>{formatPrice(customer.total_spent)}</b>
          </Typography.Paragraph>
          <Table
            rowKey="id" loading={!orders} dataSource={orders || []} pagination={false} size="small"
            columns={[
              { title: '№', dataIndex: 'id', render: id => <Link to={`/orders?open=${id}`}>#{id}</Link> },
              { title: 'Summa', dataIndex: 'total', render: formatPrice },
              { title: 'Holati', dataIndex: 'status', render: s => <Tag color={ORDER_STATUS[s].color}>{ORDER_STATUS[s].label}</Tag> },
              { title: 'Sana', dataIndex: 'created_at', render: d => dayjs(d).format('DD.MM.YYYY') },
            ]}
          />
        </>
      )}
    </Drawer>
  )
}

export default function Customers() {
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const filters = Object.fromEntries(params)
  const page = Number(filters.page || 1)

  useEffect(() => {
    setLoading(true)
    api(`/admin/customers/?${params}`).then(setData).finally(() => setLoading(false))
  }, [params])

  const update = changes => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes)) next.delete('page')
    setParams(next)
  }
  const ordering = filters.ordering || ''
  const sortOrder = key => (ordering === key ? 'ascend' : ordering === `-${key}` ? 'descend' : null)

  return (
    <>
      <Typography.Title level={3} style={{ marginTop: 0 }}>Mijozlar</Typography.Title>
      <div className="toolbar">
        <Input.Search placeholder="Ism, telefon, email" allowClear style={{ width: 260 }}
                      defaultValue={filters.search} onSearch={v => update({ search: v })} />
      </div>
      <Table
        rowKey="id" loading={loading} dataSource={data.results} scroll={{ x: 800 }}
        onRow={c => ({ onClick: () => setSelected(c), style: { cursor: 'pointer' } })}
        onChange={(_, __, s, { action }) => action === 'sort' && update({ ordering: s.order ? `${s.order === 'descend' ? '-' : ''}${s.field}` : '' })}
        pagination={{
          current: page, total: data.count, pageSize: 20, showSizeChanger: false,
          showTotal: t => `Jami: ${t}`, onChange: p => { update({ page: p === 1 ? '' : String(p) }); scrollToTable() },
        }}
        columns={[
          {
            title: 'Ism', key: 'name',
            render: (_, c) => (
              <b>{`${c.first_name} ${c.last_name}`.trim() || '—'}</b>
            ),
          },
          { title: 'Telefon', dataIndex: 'phone', render: p => p ? <a href={`tel:${p.replace(/\s/g, '')}`}>{p}</a> : '—' },
          { title: 'Email', dataIndex: 'email', render: e => e || '—' },
          { title: 'Buyurtmalar', dataIndex: 'orders_count', align: 'center', sorter: true, sortOrder: sortOrder('orders_count') },
          { title: 'Jami xarid', dataIndex: 'total_spent', align: 'right', sorter: true, sortOrder: sortOrder('total_spent'), render: formatPrice },
          {
            title: 'Ro\'yxatdan o\'tgan', dataIndex: 'date_joined', sorter: true, sortOrder: sortOrder('date_joined'),
            render: d => dayjs(d).format('DD.MM.YYYY'),
          },
        ]}
      />
      <CustomerOrders customer={selected} onClose={() => setSelected(null)} />
    </>
  )
}
