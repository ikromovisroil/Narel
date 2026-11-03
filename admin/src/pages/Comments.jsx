import { useEffect, useState } from 'react'
import {
  App, Button, Input, Modal, Popconfirm, Rate, Segmented, Select, Space, Spin, Switch, Table, Tag, Tooltip, Typography,
} from 'antd'
import { CheckCircleFilled, DeleteOutlined, LinkOutlined, MessageOutlined, ShopFilled } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router-dom'
import { scrollToTable } from '../utils'
import { api, errorText } from '../api'
import { usePerm } from '../auth'

// Izohga do'kon nomidan javob: suhbat ko'rinadi, javob saytda "Do'kon" belgisi bilan chiqadi
function ReplyModal({ comment, onClose, onSent }) {
  const { message } = App.useApp()
  const [thread, setThread] = useState(null)
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const rootId = comment ? (comment.parent || comment.id) : null

  useEffect(() => {
    setText('')
    setThread(null)
    if (!rootId) return
    // Suhbatdagi javoblar (eskidan yangiga)
    api(`/admin/comments/?parent=${rootId}&page_size=100`)
      .then(r => setThread([...r.results].reverse()))
      .catch(() => setThread([]))
  }, [rootId])

  const send = async () => {
    setSending(true)
    try {
      await api(`/admin/comments/${comment.id}/reply/`, { method: 'POST', body: { text } })
      message.success('Javob yuborildi — saytda "Do\'kon" belgisi bilan ko\'rinadi')
      onSent()
      onClose()
    } catch (err) {
      message.error(errorText(err))
    } finally {
      setSending(false)
    }
  }

  const root = comment && (comment.parent ? { author: '', text: comment.parent_text } : comment)

  return (
    <Modal
      open={Boolean(comment)} onCancel={onClose} title="Izohga javob berish" width={620}
      okText="Javob yuborish" cancelText="Bekor" onOk={send} confirmLoading={sending}
      okButtonProps={{ disabled: text.trim().length < 2 }} destroyOnHidden
    >
      {comment && (
        <>
          <Typography.Text type="secondary">
            <LinkOutlined />{' '}
            <a href={`http://localhost:5173/product/${comment.product_slug}`} target="_blank" rel="noreferrer">{comment.product_name}</a>
          </Typography.Text>
          <div className="reply-thread">
            <div className="reply-msg">
              <b>{root.author || 'Mijoz'}</b>
              {comment.rating && !comment.parent && <Rate disabled value={comment.rating} style={{ fontSize: 12, marginLeft: 8 }} />}
              <div>{root.text}</div>
            </div>
            {!thread ? <Spin size="small" /> : thread.map(r => (
              <div key={r.id} className={`reply-msg sub ${r.is_staff ? 'staff' : ''}`}>
                <b>{r.author}</b>{r.is_staff && <Tag color="orange" style={{ marginLeft: 6 }}>Do'kon</Tag>}
                <Typography.Text type="secondary" style={{ fontSize: 12, marginLeft: 6 }}>{dayjs(r.created_at).format('DD.MM HH:mm')}</Typography.Text>
                <div>{r.text}</div>
              </div>
            ))}
          </div>
          <Input.TextArea
            rows={4} maxLength={1000} showCount autoFocus value={text} onChange={e => setText(e.target.value)}
            style={{ marginBottom: 24 }} /* "5 / 1000" hisoblagichi tugmalarga yopishmasin */
            placeholder="Javobingiz... Mijoz uni mahsulot sahifasida ko'radi."
          />
        </>
      )}
    </Modal>
  )
}

export default function Comments() {
  const { message } = App.useApp()
  const perm = usePerm('comments')
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(false)
  const [reload, setReload] = useState(0)
  const [replyTo, setReplyTo] = useState(null)
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
        Mijozlarning mahsulotlarga yozgan izohlari va savollari. <b>"Javob berish"</b> orqali do'kon nomidan javob
        yozing — saytda ismingiz yonida "Do'kon" belgisi chiqadi. Nomaqbul izohni <b>yashiring</b> — saytda
        ko'rinmay qoladi, lekin o'chib ketmaydi.
      </Typography.Paragraph>

      <div className="toolbar">
        <Input.Search placeholder="Matn, muallif, mahsulot" allowClear style={{ width: 260 }}
                      defaultValue={filters.search} onSearch={v => update({ search: v })} />
        <Segmented
          value={filters.kind || ''} onChange={v => update({ kind: v })}
          options={[
            { value: '', label: 'Hammasi' }, { value: 'unanswered', label: 'Javobsiz' },
            { value: 'reviews', label: 'Izohlar' }, { value: 'replies', label: 'Javoblar' },
            { value: 'low', label: 'Past baho (1–2)' },
          ]}
        />
        <Select placeholder="Holati" allowClear style={{ width: 160 }} value={filters.is_hidden}
                options={[{ value: 'false', label: "Ko'rinadigan" }, { value: 'true', label: 'Yashirilgan' }]}
                onChange={v => update({ is_hidden: v })} />
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={data.results} scroll={{ x: 1200 }}
        rowClassName={c => (c.is_hidden ? 'row-muted' : c.is_staff ? 'row-staff' : '')}
        pagination={{
          current: page, total: data.count, pageSize: 20, showSizeChanger: false,
          showTotal: t => `Jami: ${t}`, onChange: p => { update({ page: p === 1 ? '' : String(p) }); scrollToTable() },
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
                <Space size={4} style={{ marginTop: 4 }} wrap>
                  {c.replies_count > 0 && <Tag>{c.replies_count} ta javob</Tag>}
                  {c.staff_replied && <Tag color="green" icon={<CheckCircleFilled />}>Javob berilgan</Tag>}
                  {!c.parent && !c.is_staff && !c.staff_replied && <Tag color="gold">Javob kutmoqda</Tag>}
                </Space>
              </div>
            ),
          },
          {
            title: 'Muallif', key: 'author', width: 160,
            render: (_, c) => (
              <span style={{ display: 'grid' }}>
                <b>{c.author} {c.is_staff && <Tag color="orange" icon={<ShopFilled />} style={{ marginLeft: 4 }}>Do'kon</Tag>}</b>
                {c.phone && <Typography.Text type="secondary" style={{ fontSize: 12 }}>{c.phone}</Typography.Text>}
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
          {
            title: '', key: 'a', width: 150, fixed: 'right', align: 'right',
            render: (_, c) => (
              <Space>
                {perm.add && !c.is_staff && !c.is_hidden && (
                  <Button size="small" type={c.staff_replied ? 'default' : 'primary'} icon={<MessageOutlined />}
                          onClick={() => setReplyTo(c)}>
                    Javob
                  </Button>
                )}
                {perm.delete && (
                  <Popconfirm title="Izoh o'chirilsinmi?" description={c.replies_count ? 'Unga yozilgan javoblar ham o\'chadi.' : undefined}
                              okText="Ha" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(c)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />
      {!perm.change && !perm.add && (
        <Space style={{ marginTop: 8 }}><Typography.Text type="secondary">Sizda faqat ko'rish ruxsati bor.</Typography.Text></Space>
      )}

      <ReplyModal comment={replyTo} onClose={() => setReplyTo(null)} onSent={() => setReload(r => r + 1)} />
    </>
  )
}
