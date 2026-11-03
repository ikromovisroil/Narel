import { useEffect, useMemo, useState } from 'react'
import {
  Alert, App, Avatar, Button, Checkbox, Col, Drawer, Form, Input, Popconfirm, Row, Space, Switch, Table, Tag,
  Tooltip, Typography,
} from 'antd'
import { CrownFilled, DeleteOutlined, EditOutlined, PlusOutlined, UserOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { api, applyFormErrors, errorText } from '../api'
import { useAuth, usePerm } from '../auth'

const ACTIONS = [
  { key: 'view', label: "Ko'rish", short: 'K' },
  { key: 'add', label: "Qo'shish", short: 'Q' },
  { key: 'change', label: 'Tahrirlash', short: 'T' },
  { key: 'delete', label: "O'chirish", short: 'O' },
]
const ACTION_LABEL = Object.fromEntries(ACTIONS.map(a => [a.key, a.label]))

// Tez tanlash uchun tayyor shablonlar: bo'lim -> amallar ('all' — bo'limdagi barcha amallar)
const TEMPLATES = [
  {
    key: 'operator', label: 'Operator',
    perms: { dashboard: 'all', orders: 'all', customers: 'all', products: ['view'] },
  },
  {
    key: 'content', label: 'Kontent menejer',
    perms: { products: 'all', categories: 'all', brands: 'all', banners: 'all' },
  },
  {
    key: 'manager', label: 'Menejer',
    perms: {
      dashboard: 'all', orders: 'all', products: 'all', categories: 'all', brands: 'all', banners: 'all', customers: 'all',
    },
  },
  { key: 'viewer', label: "Faqat ko'rish", perms: '*view' },
]

// Har qanday amal "ko'rish"ni ham talab qiladi; ko'rish olinsa — hammasi olinadi
function normalize(actions) {
  const set = new Set(actions)
  if (!set.has('view')) return []
  return ACTIONS.map(a => a.key).filter(a => set.has(a))
}

function PermissionMatrix({ sections, value = {}, onChange, mine, isSuper, disabled }) {
  // Xodim faqat o'zida bor amalni bera oladi
  const canGrant = (code, action) => isSuper || Boolean(mine[code]?.includes(action))
  const grantable = s => s.actions.filter(a => canGrant(s.code, a))

  const setSection = (code, actions) => {
    const next = { ...value }
    const clean = normalize(actions)
    if (clean.length) next[code] = clean
    else delete next[code]
    onChange(next)
  }

  const toggle = (s, action, checked) => {
    let current = new Set(value[s.code] || [])
    if (checked) {
      current.add(action)
      current.add('view')
    } else if (action === 'view') {
      current = new Set()
    } else {
      current.delete(action)
    }
    setSection(s.code, [...current])
  }

  const rowState = s => {
    const have = (value[s.code] || []).length
    const total = grantable(s).length
    return { checked: total > 0 && have >= total, indeterminate: have > 0 && have < total }
  }

  // Butun jadval uchun "hammasi"
  const allGrantable = sections.reduce((n, s) => n + grantable(s).length, 0)
  const allHave = sections.reduce((n, s) => n + (value[s.code] || []).filter(a => canGrant(s.code, a)).length, 0)
  const toggleAll = checked => {
    const next = {}
    if (checked) sections.forEach(s => { const g = grantable(s); if (g.length) next[s.code] = normalize(g) })
    onChange(next)
  }

  const applyTemplate = t => {
    const next = {}
    sections.forEach(s => {
      const wanted = t.perms === '*view' ? ['view'] : t.perms[s.code] === 'all' ? s.actions : (t.perms[s.code] || [])
      const clean = normalize(wanted.filter(a => s.actions.includes(a) && canGrant(s.code, a)))
      if (clean.length) next[s.code] = clean
    })
    onChange(next)
  }

  return (
    <>
      <Space wrap style={{ marginBottom: 12 }}>
        <Typography.Text type="secondary">Shablon:</Typography.Text>
        {TEMPLATES.map(t => (
          <Button key={t.key} size="small" disabled={disabled} onClick={() => applyTemplate(t)}>{t.label}</Button>
        ))}
      </Space>

      <div className="perm-table">
        <div className="perm-row perm-head">
          <span>Bo'lim</span>
          <Checkbox
            disabled={disabled || !allGrantable} checked={allGrantable > 0 && allHave >= allGrantable}
            indeterminate={allHave > 0 && allHave < allGrantable} onChange={e => toggleAll(e.target.checked)}
          >
            Hammasi
          </Checkbox>
          {ACTIONS.map(a => <span key={a.key} className="perm-col">{a.label}</span>)}
        </div>
        {sections.map(s => {
          const state = rowState(s)
          return (
            <div key={s.code} className="perm-row">
              <span className="perm-title">{s.title}</span>
              <Checkbox
                {...state} disabled={disabled || !grantable(s).length}
                onChange={e => setSection(s.code, e.target.checked ? grantable(s) : [])}
              >
                <span className="perm-mobile-label">Hammasi</span>
              </Checkbox>
              {ACTIONS.map(a => (
                <span key={a.key} className="perm-col">
                  {s.actions.includes(a.key) ? (
                    <Tooltip title={canGrant(s.code, a.key) ? '' : "Sizda bu ruxsat yo'q — bera olmaysiz"}>
                      <Checkbox
                        checked={(value[s.code] || []).includes(a.key)}
                        disabled={disabled || !canGrant(s.code, a.key)}
                        onChange={e => toggle(s, a.key, e.target.checked)}
                      >
                        <span className="perm-mobile-label">{a.label}</span>
                      </Checkbox>
                    </Tooltip>
                  ) : <span className="perm-na">—</span>}
                </span>
              ))}
            </div>
          )
        })}
      </div>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>
        Qo'shish, tahrirlash yoki o'chirish belgilansa, ko'rish ham avtomatik beriladi. "—" — bu bo'limda shunday amal yo'q.
        {!isSuper && " O'zingizda yo'q ruxsatlarni boshqalarga bera olmaysiz."}
      </Typography.Paragraph>
    </>
  )
}

function StaffDrawer({ staff, sections, onClose, onSaved }) {
  const { message } = App.useApp()
  const { user, refreshMe } = useAuth()
  const perm = usePerm('staff')
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const isNew = staff && !staff.id
  const isSelf = staff?.is_self
  const superFlag = Form.useWatch('is_superuser', form)
  const lockedSuper = staff?.is_superuser && !user.is_superuser
  const canSave = isNew ? perm.add : perm.change
  const readOnly = lockedSuper || !canSave

  useEffect(() => {
    if (staff) {
      form.resetFields()
      form.setFieldsValue({ is_active: true, is_superuser: false, permissions: {}, ...staff, password: '' })
    }
  }, [staff, form])

  const save = async values => {
    setSaving(true)
    const body = { ...values }
    if (!body.password) delete body.password
    if (isSelf) { delete body.permissions; delete body.is_active }
    if (!user.is_superuser) delete body.is_superuser
    try {
      await api(isNew ? '/admin/staff/' : `/admin/staff/${staff.id}/`, { method: isNew ? 'POST' : 'PATCH', body })
      message.success(isNew ? 'Xodim qo\'shildi' : 'Saqlandi')
      if (isSelf) refreshMe()
      onSaved()
      onClose()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error({ content: errorText(err), duration: 6 })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Drawer
      open={Boolean(staff)} onClose={onClose} size={720}
      title={isNew ? 'Yangi xodim' : `${staff?.first_name || staff?.username || ''} — ${readOnly ? "ko'rish" : 'tahrirlash'}`}
      extra={!readOnly && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      {staff && (
        <Form form={form} layout="vertical" onFinish={save} disabled={readOnly} requiredMark={false}>
          {lockedSuper && <Alert type="warning" showIcon style={{ marginBottom: 16 }} title="Super adminni faqat super admin o'zgartira oladi." />}
          {isSelf && <Alert type="info" showIcon style={{ marginBottom: 16 }} title="Bu sizning hisobingiz: o'z ruxsatlaringiz va holatingizni o'zgartira olmaysiz." />}

          <Typography.Title level={5} style={{ marginTop: 0 }}>Shaxsiy ma'lumotlar</Typography.Title>
          <Row gutter={12}>
            <Col xs={24} sm={12}><Form.Item name="first_name" label="Ism"><Input /></Form.Item></Col>
            <Col xs={24} sm={12}><Form.Item name="last_name" label="Familiya"><Input /></Form.Item></Col>
            <Col xs={24} sm={12}><Form.Item name="position" label="Lavozimi"><Input placeholder="Masalan: Operator" /></Form.Item></Col>
            <Col xs={24} sm={12}><Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Email noto\'g\'ri' }]}><Input /></Form.Item></Col>
          </Row>

          <Typography.Title level={5}>Kirish ma'lumotlari</Typography.Title>
          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item name="username" label="Login" rules={[{ required: true, message: 'Loginni kiriting' }]}
                         extra="Admin panelga shu login bilan kiradi">
                <Input autoComplete="off" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="password" label={isNew ? 'Parol' : 'Yangi parol'}
                rules={isNew ? [{ required: true, message: 'Parolni kiriting' }] : []}
                extra={isNew ? 'Kamida 8 belgi, oddiy so\'z bo\'lmasin' : 'O\'zgartirmaslik uchun bo\'sh qoldiring'}
              >
                <Input.Password autoComplete="new-password" />
              </Form.Item>
            </Col>
          </Row>
          <Space size="large" wrap>
            <Form.Item name="is_active" label="Faol" valuePropName="checked" extra="O'chirilsa panelga kira olmaydi">
              <Switch disabled={isSelf || readOnly} />
            </Form.Item>
            {user.is_superuser && (
              <Form.Item name="is_superuser" label="Super admin" valuePropName="checked" extra="Hamma narsaga to'liq ruxsat">
                <Switch disabled={isSelf} />
              </Form.Item>
            )}
          </Space>

          <Typography.Title level={5}>Ruxsatlar</Typography.Title>
          {superFlag ? (
            <Alert type="success" showIcon title="Super admin barcha bo'limlarda hamma amallarni bajara oladi." />
          ) : (
            <Form.Item name="permissions" noStyle>
              <PermissionMatrix
                sections={sections} mine={user.permissions} isSuper={user.is_superuser}
                disabled={isSelf || readOnly}
              />
            </Form.Item>
          )}
        </Form>
      )}
    </Drawer>
  )
}

export default function Staff() {
  const { message } = App.useApp()
  const perm = usePerm('staff')
  const [list, setList] = useState(null)
  const [sections, setSections] = useState([])
  const [editing, setEditing] = useState(null)
  const [search, setSearch] = useState('')

  const load = () => api('/admin/staff/').then(setList)
  useEffect(() => {
    load()
    api('/admin/staff/sections/').then(setSections)
  }, [])

  const byCode = useMemo(() => Object.fromEntries(sections.map(s => [s.code, s])), [sections])

  const remove = async s => {
    try {
      await api(`/admin/staff/${s.id}/`, { method: 'DELETE' })
      message.success('Xodim o\'chirildi')
      load()
    } catch (err) {
      message.error(errorText(err))
    }
  }

  const rows = (list || []).filter(s => [s.username, s.first_name, s.last_name, s.position, s.email]
    .join(' ').toLowerCase().includes(search.toLowerCase()))

  const permTag = (code, actions) => {
    const section = byCode[code]
    const full = section && actions.length >= section.actions.length
    const onlyView = actions.length === 1
    return (
      <Tooltip key={code} title={actions.map(a => ACTION_LABEL[a]).join(', ')}>
        <Tag color={full ? 'green' : onlyView ? 'blue' : 'gold'}>
          {section ? section.title.split(' (')[0] : code}
          {!full && !onlyView && ` · ${actions.filter(a => a !== 'view').map(a => ACTIONS.find(x => x.key === a).short).join('')}`}
        </Tag>
      </Tooltip>
    )
  }

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Xodimlar</Typography.Title>
        {perm.add && <Button type="primary" icon={<PlusOutlined />} onClick={() => setEditing({})}>Xodim qo'shish</Button>}
      </div>
      <Typography.Paragraph type="secondary">
        Admin panelga kira oladigan xodimlar. Har bir xodimga faqat kerakli amallarni bering.
        Belgilar: <Tag color="green" style={{ marginInlineEnd: 4 }}>hammasi</Tag>
        <Tag color="gold" style={{ marginInlineEnd: 4 }}>qisman (Q — qo'shish, T — tahrirlash, O — o'chirish)</Tag>
        <Tag color="blue">faqat ko'rish</Tag>
      </Typography.Paragraph>
      <div className="toolbar">
        <Input.Search placeholder="Ism, login, lavozim" allowClear style={{ width: 260 }} onChange={e => setSearch(e.target.value)} />
      </div>

      <Table
        rowKey="id" loading={!list} dataSource={rows} pagination={false} scroll={{ x: 900 }}
        columns={[
          {
            title: 'Xodim', key: 'name',
            render: (_, s) => (
              <Space>
                <Avatar icon={<UserOutlined />} style={{ background: s.is_superuser ? '#ff6a00' : '#1f5eff' }} />
                <span style={{ display: 'grid' }}>
                  <b>
                    {`${s.first_name} ${s.last_name}`.trim() || s.username}
                    {s.is_self && <Tag style={{ marginLeft: 6 }}>siz</Tag>}
                  </b>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>{s.username}{s.position && ` · ${s.position}`}</Typography.Text>
                </span>
              </Space>
            ),
          },
          {
            title: 'Holati', dataIndex: 'is_active', width: 110,
            render: a => (a ? <Tag color="green">Faol</Tag> : <Tag color="red">Bloklangan</Tag>),
          },
          {
            title: 'Ruxsatlar', key: 'perms',
            render: (_, s) => (s.is_superuser ? <Tag icon={<CrownFilled />} color="orange">Super admin — hammasi</Tag> : (
              Object.keys(s.permissions).length
                ? <Space size={[4, 4]} wrap>{Object.entries(s.permissions).map(([c, a]) => permTag(c, a))}</Space>
                : <Typography.Text type="secondary">Ruxsat berilmagan</Typography.Text>
            )),
          },
          {
            title: 'Oxirgi kirish', dataIndex: 'last_login', width: 150,
            render: d => (d ? dayjs(d).format('DD.MM.YYYY HH:mm') : <Typography.Text type="secondary">hali kirmagan</Typography.Text>),
          },
          {
            title: '', key: 'a', width: 100, align: 'right', fixed: 'right',
            render: (_, s) => (
              <Space>
                <Tooltip title={perm.change ? 'Tahrirlash' : "Ko'rish"}>
                  <Button size="small" icon={<EditOutlined />} onClick={() => setEditing(s)} />
                </Tooltip>
                {perm.delete && !s.is_self && (
                  <Popconfirm
                    title={`${s.username} o'chirilsinmi?`}
                    description="Vaqtincha to'xtatish uchun o'chirish o'rniga bloklang."
                    okText="Ha, o'chirish" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(s)}
                  >
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />

      <StaffDrawer staff={editing} sections={sections} onClose={() => setEditing(null)} onSaved={load} />
    </>
  )
}
