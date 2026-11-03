import { useEffect, useState } from 'react'
import { App, Button, Input, Popconfirm, Rate, Segmented, Select, Space, Switch, Table, Tag, Tooltip, Typography } from 'antd'
import { DeleteOutlined, LinkOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router-dom'
import { api, errorText } from '../api'
import { usePerm } from '../auth'

export default function Comments() {
  const { message } = App.useApp()
  const perm = usePerm('comments')
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [reload, setReload] = useState(0)
  const filters = Object.fromEntries(params)
  const page = Number(filters.page || 1)

  useEffect(() => {
    setLoading(true)
    api(`/admin/comments/?${params}`).then(setData).finally(() => setLoading(false))
  }, [params, reload])

  const update = changes => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes)) next.delete('page')
    setParams(next)
  }

  const setHidden = async (c, is_hidden) => {
    try {
      const saved = await api(`/admin/comments/${c.id}/`, { method: 'PATCH', body: { is_hidden } })
      setData(d => ({ ...d, results: d.results.map(x => (x.id === c.id ? { ...x, ...saved } : x)) }))
      message.success(is_hidden ? 'Izoh yashirildi — saytda ko\'rinmaydi' : 'Izoh yana ko\'rinadi')
    } catch (err) {
      message.error(errorText(err))
    }
  }

  const remove = async c => {
    try {
      await api(`/admin/comments/${c.id}/`, { method: 'DELETE' })
      message.success('O\'chirildi')
      setReload(r => r + 1)
    } catch (err) {
      message.error(errorText(err))
    }
  }

  return (
    <>
      <Typography.Title level={3} style={{ marginTop: 0 }}>Izohlar</Typography.Title>
      <Typography.Paragraph type="secondary">
        Mijozlarning mahsulotlarga yozgan izohlari va javoblari. Nomaqbul izohni <b>yashiring</b> — u saytda
        ko'rinmay qoladi, lekin o'chib ketmaydi. Mijozga javob berish uchun saytda o'z hisobingiz bilan kirib,
        mahsulot sahifasidagi izohga "Javob berish"ni bosing — ismingiz yonida "Do'kon" belgisi chiqadi.
      </Typography.Paragraph>

      <div className="toolbar">
        <Input.Search placeholder="Matn, muallif, mahsulot" allowClear style={{ width: 260 }}
                      defaultValue={filters.search} onSearch={v => update({ search: v })} />
        <Segmented
          value={filters.kind || ''} onChange={v => update({ kind: v })}
          options={[
            { value: '', label: 'Hammasi' }, { value: 'reviews', label: 'Izohlar' },
            { value: 'replies', label: 'Javoblar' }, { value: 'low', label: 'Past baho (1–2)' },
          ]}
        />
        <Select placeholder="Holati" allowClear style={{ width: 160 }} value={filters.is_hidden}
                options={[{ value: 'false', label: "Ko'rinadigan" }, { value: 'true', label: 'Yashirilgan' }]}
                onChange={v => update({ is_hidden: v })} />
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={data.results} scroll={{ x: 1100 }}
        rowClassName={c => (c.is_hidden ? 'row-muted' : '')}
        pagination={{
          current: page, total: data.count, pageSize: 20, showSizeChanger: false,
          showTotal: t => `Jami: ${t}`, onChange: p => update({ page: p === 1 ? '' : String(p) }),
        }}
        columns={[
          {
            title: 'Izoh', key: 'text', width: 340,
            render: (_, c) => (
              <div style={{ maxWidth: 460 }}>
                {c.parent && (
                  <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }} ellipsis>
                    ↳ Javob: «{c.parent_text}»
                  </Typography.Text>
                )}
                <div style={{ whiteSpace: 'pre-line' }}>{c.text}</div>
                {c.replies_count > 0 && <Tag style={{ marginTop: 4 }}>{c.replies_count} ta javob</Tag>}
              </div>
            ),
          },
          {
            title: 'Muallif', key: 'author', width: 160,
            render: (_, c) => (
              <span style={{ display: 'grid' }}>
                <b>{c.author}</b>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>{c.username}</Typography.Text>
              </span>
            ),
          },
          {
            title: 'Mahsulot', key: 'product', width: 200,
            render: (_, c) => (
              <a href={`http://localhost:5173/product/${c.product_slug}`} target="_blank" rel="noreferrer">
                <LinkOutlined /> {c.product_name}
              </a>
            ),
          },
          {
            title: 'Baho', dataIndex: 'rating', width: 130,
            render: r => (r ? <Rate disabled value={r} style={{ fontSize: 13 }} /> : <Typography.Text type="secondary">—</Typography.Text>),
          },
          { title: 'Sana', dataIndex: 'created_at', width: 140, render: d => dayjs(d).format('DD.MM.YYYY HH:mm') },
          {
            title: 'Saytda', dataIndex: 'is_hidden', width: 90, align: 'center',
            render: (h, c) => (
              <Tooltip title={h ? 'Yashirilgan' : "Ko'rinadi"}>
                <Switch size="small" checked={!h} disabled={!perm.change} onChange={v => setHidden(c, !v)} />
              </Tooltip>
            ),
          },
          ...(perm.delete ? [{
            title: '', key: 'a', width: 60, fixed: 'right',
            render: (_, c) => (
              <Popconfirm title="Izoh o'chirilsinmi?" description={c.replies_count ? 'Unga yozilgan javoblar ham o\'chadi.' : undefined}
                          okText="Ha" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(c)}>
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            ),
          }] : []),
        ]}
      />
      {!perm.change && <Space style={{ marginTop: 8 }}><Typography.Text type="secondary">Sizda faqat ko'rish ruxsati bor.</Typography.Text></Space>}
    </>
  )
}
