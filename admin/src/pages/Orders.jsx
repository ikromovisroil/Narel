import { useCallback, useEffect, useState } from 'react'
import {
  App, Button, DatePicker, Descriptions, Drawer, Input, Popconfirm, Select, Space, Steps, Table, Tag, Typography,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { DELIVERY, formatPrice, options, ORDER_STATUS, PAYMENT } from '../utils'
import { useCanEdit } from '../auth'

const FLOW = ['new', 'confirmed', 'shipped', 'delivered']

function OrderDrawer({ id, onClose, onChanged }) {
  const canEdit = useCanEdit('orders')
  const { message } = App.useApp()
  const [order, setOrder] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (id) api(`/admin/orders/${id}/`).then(setOrder).catch(err => message.error(errorText(err)))
    else setOrder(null)
  }, [id, message])

  const setStatus = async status => {
    setSaving(true)
    try {
      const o = await api(`/admin/orders/${id}/`, { method: 'PATCH', body: { status } })
      setOrder(o)
      onChanged()
      window.dispatchEvent(new Event('orders-changed'))
      message.success(`Holat: ${ORDER_STATUS[status].label}`)
    } catch (err) {
      message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  const cancelled = order?.status === 'cancelled'
  const step = order ? FLOW.indexOf(order.status) : 0
  const next = FLOW[step + 1]

  return (
    <Drawer open={Boolean(id)} onClose={onClose} size={640} title={order ? `Buyurtma #${order.id}` : 'Yuklanmoqda...'}
            loading={!order}
            extra={order && !cancelled && canEdit && (
              <Popconfirm title="Buyurtmani bekor qilasizmi?" description="Mahsulotlar omborga qaytariladi."
                          okText="Ha, bekor qilish" cancelText="Yo'q" okButtonProps={{ danger: true }}
                          onConfirm={() => setStatus('cancelled')}>
                <Button danger disabled={saving}>Bekor qilish</Button>
              </Popconfirm>
            )}>
      {order && (
        <Space orientation="vertical" size="large" style={{ width: '100%' }}>
          {cancelled ? <Tag color="red" style={{ fontSize: 14, padding: 6 }}>Bekor qilingan</Tag> : (
            <>
              <Steps current={step} size="small" items={FLOW.map(s => ({ title: ORDER_STATUS[s].label }))} />
              {next && canEdit && (
                <Button type="primary" block loading={saving} onClick={() => setStatus(next)}>
                  "{ORDER_STATUS[next].label}" holatiga o'tkazish
                </Button>
              )}
            </>
          )}

          <Descriptions column={1} bordered size="small" items={[
            { label: 'Mijoz', children: order.full_name },
            { label: 'Telefon', children: <a href={`tel:${order.phone}`}>{order.phone}</a> },
            { label: 'Hisob', children: order.username },
            { label: 'Yetkazish', children: DELIVERY[order.delivery_method] },
            { label: 'Manzil', children: order.address || '—' },
            { label: 'To\'lov', children: PAYMENT[order.payment_method] },
            { label: 'Izoh', children: order.note || '—' },
            { label: 'Sana', children: dayjs(order.created_at).format('DD.MM.YYYY HH:mm') },
          ]} />

          <Table
            rowKey="product" dataSource={order.items} pagination={false} size="small"
            columns={[
              { title: 'Mahsulot', dataIndex: 'product_name' },
              { title: 'Narx', dataIndex: 'price', render: formatPrice },
              { title: 'Soni', dataIndex: 'quantity', align: 'center' },
              { title: 'Jami', dataIndex: 'subtotal', render: formatPrice, align: 'right' },
            ]}
            summary={() => (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={3}><b>Umumiy summa</b></Table.Summary.Cell>
                <Table.Summary.Cell index={1} align="right"><b>{formatPrice(order.total)}</b></Table.Summary.Cell>
              </Table.Summary.Row>
            )}
          />
        </Space>
      )}
    </Drawer>
  )
}

export default function Orders() {
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState(params.get('search') || '')

  const filters = Object.fromEntries(params)
  const page = Number(filters.page || 1)

  // "open" (ochiq drawer) o'zgarganda ro'yxatni qayta yuklamaymiz
  const listQuery = (() => {
    const q = new URLSearchParams(params)
    q.delete('open')
    return q.toString()
  })()

  const load = useCallback(() => {
    setLoading(true)
    api(`/admin/orders/?${listQuery}`)
      .then(setData)
      .finally(() => setLoading(false))
  }, [listQuery])

  useEffect(load, [load])

  const update = changes => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes) && !('open' in changes)) next.delete('page')
    setParams(next)
  }

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Buyurtmalar</Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={load}>Yangilash</Button>
      </div>

      <div className="toolbar">
        <Input.Search placeholder="№, ism, telefon" allowClear value={search} style={{ width: 240 }}
                      onChange={e => setSearch(e.target.value)} onSearch={v => update({ search: v })} />
        <Select placeholder="Holati" allowClear style={{ width: 170 }} value={filters.status}
                options={options(ORDER_STATUS)} onChange={v => update({ status: v })} />
        <Select placeholder="To'lov usuli" allowClear style={{ width: 170 }} value={filters.payment_method}
                options={options(PAYMENT)} onChange={v => update({ payment_method: v })} />
        <DatePicker.RangePicker
          format="DD.MM.YYYY"
          value={filters.created_at__date__gte ? [dayjs(filters.created_at__date__gte), dayjs(filters.created_at__date__lte)] : null}
          onChange={r => update({
            created_at__date__gte: r?.[0]?.format('YYYY-MM-DD'),
            created_at__date__lte: r?.[1]?.format('YYYY-MM-DD'),
          })}
        />
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={data.results} scroll={{ x: 900 }}
        onRow={o => ({ onClick: () => update({ open: String(o.id) }), style: { cursor: 'pointer' } })}
        pagination={{
          current: page, total: data.count, pageSize: 20, showSizeChanger: false,
          showTotal: t => `Jami: ${t}`, onChange: p => update({ page: p === 1 ? '' : String(p) }),
        }}
        columns={[
          { title: '№', dataIndex: 'id', render: id => <b>#{id}</b>, width: 80 },
          { title: 'Mijoz', dataIndex: 'full_name' },
          { title: 'Telefon', dataIndex: 'phone' },
          { title: 'Mahsulot', dataIndex: 'items_count', render: n => `${n || 0} dona`, align: 'center' },
          { title: 'Summa', dataIndex: 'total', render: formatPrice, align: 'right' },
          { title: 'To\'lov', dataIndex: 'payment_method', render: p => PAYMENT[p] },
          { title: 'Yetkazish', dataIndex: 'delivery_method', render: d => DELIVERY[d] },
          { title: 'Holati', dataIndex: 'status', render: s => <Tag color={ORDER_STATUS[s].color}>{ORDER_STATUS[s].label}</Tag> },
          { title: 'Sana', dataIndex: 'created_at', render: d => dayjs(d).format('DD.MM.YYYY HH:mm') },
        ]}
      />

      <OrderDrawer id={filters.open} onClose={() => update({ open: '' })} onChanged={load} />
    </>
  )
}
