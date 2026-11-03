import { useCallback, useEffect, useState } from 'react'
import {
  Alert, App, Button, DatePicker, Descriptions, Drawer, Input, Popconfirm, Select, Space, Steps, Table, Tag, Typography,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { DELIVERY, formatPrice, options, ORDER_STATUS, PAYMENT } from '../utils'
import { useCanEdit } from '../auth'

const FLOW = ['new', 'confirmed', 'shipped', 'delivered']

// Kuryer buyurtmasi: qabul qilishda sana majburiy, keyin o'zgartirish (kechikish izohi bilan)
function DeliveryDateBox({ order, canEdit, onSaved }) {
  const { message } = App.useApp()
  const today = dayjs().startOf('day')
  const initial = order.expected_date && !dayjs(order.expected_date).isBefore(today) ? dayjs(order.expected_date) : null
  const [date, setDate] = useState(initial)
  const [note, setNote] = useState(order.delay_note || '')
  const [saving, setSaving] = useState(false)
  const promised = order.original_expected_date ? dayjs(order.original_expected_date) : null
  const finished = ['delivered', 'cancelled'].includes(order.status)
  const fmt = d => dayjs(d).format('DD.MM.YYYY')

  const save = async body => {
    setSaving(true)
    try {
      onSaved(await api(`/admin/orders/${order.id}/`, { method: 'PATCH', body }))
      message.success(body.status ? 'Buyurtma qabul qilindi — mijoz yetkazish sanasini ko\'radi' : 'Sana saqlandi — mijoz yangisini ko\'radi')
    } catch (err) {
      message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  // Yetkazilgan yoki bekor qilingan — faqat ko'rish
  if (finished || !canEdit) {
    return (
      <div className="date-box">
        <b>Taxminiy yetkazish:</b> {order.expected_date ? fmt(order.expected_date) : '—'}
        {promised && order.expected_date !== order.original_expected_date && (
          <Typography.Text type="secondary"> (va'da: {fmt(promised)})</Typography.Text>
        )}
        {finished && <Typography.Text type="secondary"> · yakunlangan buyurtma, sanani o'zgartirib bo'lmaydi</Typography.Text>}
      </div>
    )
  }

  if (order.status === 'new') {
    return (
      <div className="date-box accept">
        <b>Buyurtmani qabul qilish</b>
        <Typography.Text type="secondary">
          Mijozga yetkazib beriladigan taxminiy sanani tanlang — u "Buyurtmalarim"da ko'rinadi. Sana tanlanmasa qabul qilib bo'lmaydi.
        </Typography.Text>
        <Space wrap>
          <DatePicker format="DD.MM.YYYY" placeholder="Yetkazish sanasi" value={date} onChange={setDate}
                      disabledDate={d => d.isBefore(today)} status={date ? '' : 'warning'} />
          <Button type="primary" loading={saving} disabled={!date}
                  onClick={() => save({ status: 'confirmed', expected_date: date.format('YYYY-MM-DD') })}>
            Qabul qilish
          </Button>
        </Space>
      </div>
    )
  }

  // Tasdiqlangan / Yuborilgan — sanani o'zgartirish mumkin
  const later = date && promised && date.isAfter(promised, 'day')
  const changed = date && date.format('YYYY-MM-DD') !== order.expected_date
  return (
    <div className={`date-box ${order.is_delayed ? 'late' : ''}`}>
      <b>Taxminiy yetkazish</b>
      {promised && <Typography.Text type="secondary">Mijozga va'da qilingan sana: {fmt(promised)}</Typography.Text>}
      <Space wrap>
        <DatePicker format="DD.MM.YYYY" value={date} onChange={setDate} allowClear={false}
                    disabledDate={d => d.isBefore(today)} />
        <Button loading={saving} disabled={!date || (!changed && note === (order.delay_note || ''))}
                onClick={() => save({ expected_date: date.format('YYYY-MM-DD'), delay_note: later ? note : '' })}>
          Sanani saqlash
        </Button>
      </Space>
      {later && (
        <>
          <Alert type="warning" showIcon
                 title="Sana va'da qilinganidan keyinga surilmoqda — mijozga kechikish uchun uzr xabari ko'rsatiladi." />
          <Typography.Text type="secondary">Sababi (ixtiyoriy — yozmasangiz ham saqlanadi):</Typography.Text>
          <Input.TextArea rows={2} maxLength={255} showCount value={note} onChange={e => setNote(e.target.value)}
                          placeholder="Mijozga ko'rinadi. Masalan: Ombordan kech yetib keldi"
                          style={{ marginBottom: 16 }} />
        </>
      )}
      {order.is_delayed && !later && (
        <Alert type="error" showIcon title="Yetkazish sanasi o'tib ketdi — yangi sanani belgilang, mijozga uzr xabari chiqmoqda." />
      )}
    </div>
  )
}

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
              {next && canEdit && !(order.status === 'new' && order.delivery_method === 'courier') && (
                <Button type="primary" block loading={saving} onClick={() => setStatus(next)}>
                  "{ORDER_STATUS[next].label}" holatiga o'tkazish
                </Button>
              )}
            </>
          )}

          {order.delivery_method === 'courier' && (
            <DeliveryDateBox
              key={`${order.status}-${order.expected_date}`} order={order} canEdit={canEdit}
              onSaved={o => { setOrder(o); onChanged(); window.dispatchEvent(new Event('orders-changed')) }}
            />
          )}

          <Descriptions column={1} bordered size="small" items={[
            { label: 'Mijoz', children: order.full_name },
            { label: 'Telefon', children: <a href={`tel:${order.phone}`}>{order.phone}</a> },
            { label: 'Hisob', children: order.username },
            { label: 'Yetkazish', children: DELIVERY[order.delivery_method] },
            ...(order.delivery_method === 'pickup' ? [{ label: 'Filial', children: <b>{order.pickup_point || '—'}</b> }] : []),
            { label: 'Manzil', children: order.address || '—' },
            { label: 'To\'lov', children: PAYMENT[order.payment_method] },
            { label: 'Izoh', children: order.note || '—' },
            { label: 'Sana', children: dayjs(order.created_at).format('DD.MM.YYYY HH:mm') },
            ...(order.delivery_method === 'courier' ? [
              { label: 'Yetkazish narxi', children: Number(order.delivery_price) ? formatPrice(order.delivery_price) : 'Bepul' },
            ] : []),
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
          {
            title: 'Holati', dataIndex: 'status',
            render: (st, o) => (
              <Space size={4} wrap>
                <Tag color={ORDER_STATUS[st].color}>{ORDER_STATUS[st].label}</Tag>
                {o.is_delayed && <Tag color="red">Kechikmoqda</Tag>}
              </Space>
            ),
          },
          {
            title: 'Yetkazish sanasi', dataIndex: 'expected_date',
            render: d => (d ? dayjs(d).format('DD.MM.YYYY') : <Typography.Text type="secondary">—</Typography.Text>),
          },
          { title: 'Sana', dataIndex: 'created_at', render: d => dayjs(d).format('DD.MM.YYYY HH:mm') },
        ]}
      />

      <OrderDrawer id={filters.open} onClose={() => update({ open: '' })} onChanged={load} />
    </>
  )
}
