import { useCallback, useEffect, useState } from 'react'
import {
  Alert, App, Button, Card, Col, Empty, Form, Input, InputNumber, Modal, Popconfirm, Row, Space, Spin, Switch, Tag, Typography,
} from 'antd'
import {
  CarOutlined, DeleteOutlined, EditOutlined, EnvironmentOutlined, PhoneOutlined, PlusOutlined, ShopOutlined,
} from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import { useCanEdit } from '../auth'
import { moneyInput } from '../utils'

// Filial qo'shish / tahrirlash oynasi
function BranchModal({ branch, onClose, onSaved }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const isNew = !branch?.id

  useEffect(() => {
    form.resetFields()
    if (branch) form.setFieldsValue({ is_active: true, order: 0, ...branch })
  }, [branch, form])

  const save = async values => {
    setSaving(true)
    try {
      await api(isNew ? '/admin/branches/' : `/admin/branches/${branch.id}/`, { method: isNew ? 'POST' : 'PATCH', body: values })
      message.success(isNew ? "Filial qo'shildi" : 'Saqlandi')
      onSaved()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error({ content: errorText(err), duration: 6 })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={!!branch} title={isNew ? 'Yangi filial' : 'Filialni tahrirlash'} onCancel={onClose}
      onOk={() => form.submit()} okText="Saqlash" cancelText="Bekor qilish" confirmLoading={saving} destroyOnHidden width={640}
    >
      <Form form={form} layout="vertical" onFinish={save}>
        <Row gutter={12}>
          <Col xs={24} sm={12}>
            <Form.Item name="name" label="Nomi" rules={[{ required: true, message: 'Nomini kiriting' }]}>
              <Input placeholder="Masalan: Chilonzor filiali" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}><Form.Item name="name_ru" label="Nomi (ruscha)"><Input /></Form.Item></Col>
          <Col xs={24} sm={12}>
            <Form.Item name="address" label="Manzil" rules={[{ required: true, message: 'Manzilni kiriting' }]}><Input /></Form.Item>
          </Col>
          <Col xs={24} sm={12}><Form.Item name="address_ru" label="Manzil (ruscha)"><Input /></Form.Item></Col>
          <Col xs={24} sm={12}>
            <Form.Item name="phone" label="Telefon" rules={[{ required: true, message: 'Telefonni kiriting' }]}>
              <Input placeholder="+998 71 000 00 00" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="map_url" label="Xaritadagi havola"><Input placeholder="https://..." /></Form.Item>
          </Col>
          <Col xs={24} sm={12}><Form.Item name="working_hours" label="Ish vaqti"><Input placeholder="Har kuni 9:00–21:00" /></Form.Item></Col>
          <Col xs={24} sm={12}><Form.Item name="working_hours_ru" label="Ish vaqti (ruscha)"><Input /></Form.Item></Col>
          <Col span={12}>
            <Form.Item name="order" label="Tartib raqami"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="is_active" label="Faol" valuePropName="checked"><Switch /></Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  )
}

// Olib ketish filiallari ro'yxati
function Branches({ canEdit, onChange }) {
  const { message } = App.useApp()
  const [items, setItems] = useState(null)
  const [editing, setEditing] = useState(null)

  const load = useCallback(() => api('/admin/branches/').then(list => { setItems(list); onChange?.(list) }), [onChange])
  useEffect(() => { load() }, [load])

  const remove = async b => {
    try {
      await api(`/admin/branches/${b.id}/`, { method: 'DELETE' })
      message.success("Filial o'chirildi")
      load()
    } catch (err) {
      message.error({ content: errorText(err), duration: 6 })
    }
  }

  if (!items) return <Spin />
  return (
    <>
      {!items.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Filial yo'q" />}
      <div className="branch-list">
        {items.map(b => (
          <div key={b.id} className={`branch-item${b.is_active ? '' : ' off'}`}>
            <div className="branch-main">
              <Space size={6} wrap>
                <b>{b.name}</b>
                {!b.is_active && <Tag>O'chiq</Tag>}
                {b.orders_count > 0 && <Tag color="blue">{b.orders_count} ta buyurtma</Tag>}
              </Space>
              <div className="branch-meta"><EnvironmentOutlined /> {b.address}</div>
              <div className="branch-meta">
                <PhoneOutlined /> {b.phone}{b.working_hours ? ` · ${b.working_hours}` : ''}
              </div>
            </div>
            {canEdit && (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => setEditing(b)} />
                <Popconfirm
                  title="Filialni o'chirasizmi?"
                  description={b.orders_count ? "Eski buyurtmalarda filial manzili saqlanib qoladi." : undefined}
                  okText="O'chirish" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(b)}
                >
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            )}
          </div>
        ))}
      </div>
      {canEdit && (
        <Button
          icon={<PlusOutlined />} type="dashed" block style={{ marginTop: 8 }}
          onClick={() => setEditing({ order: (items.at(-1)?.order || 0) + 1 })}
        >
          Filial qo'shish
        </Button>
      )}
      <BranchModal branch={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load() }} />
    </>
  )
}

// Sozlamalar: yetkazib berish, olib ketish filiallari va asosiy aloqa
export default function StoreSettingsCard() {
  const { message } = App.useApp()
  const canEdit = useCanEdit('settings')
  const [form] = Form.useForm()
  const [loaded, setLoaded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [activeBranches, setActiveBranches] = useState(null)
  const delivery = Form.useWatch('delivery_enabled', form)
  const pickup = Form.useWatch('pickup_enabled', form)
  const onBranches = useCallback(list => setActiveBranches(list.filter(b => b.is_active).length), [])

  useEffect(() => {
    api('/admin/store-settings/').then(s => { form.setFieldsValue(s); setLoaded(true) })
  }, [form])

  const save = async values => {
    setSaving(true)
    try {
      form.setFieldsValue(await api('/admin/store-settings/', { method: 'PATCH', body: values }))
      message.success('Saqlandi')
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error({ content: errorText(err), duration: 6 })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card
      title="Do'kon va yetkazib berish" style={{ marginBottom: 16 }}
      extra={canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      {!loaded ? <Spin /> : null}
      <Form form={form} layout="vertical" onFinish={save} disabled={!canEdit} style={{ display: loaded ? 'block' : 'none' }}>
        <Row gutter={16}>
          <Col xs={24} lg={12}>
            <div className="setting-box">
              <div className="setting-box-head">
                <CarOutlined /> <b>Yetkazib berish</b>
                <Form.Item name="delivery_enabled" valuePropName="checked" noStyle><Switch /></Form.Item>
              </div>
              <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
                Yoqiq bo'lsa — mijoz "Kuryer orqali"ni tanlab, manzilini kiritadi va buyurtma uyiga yetkaziladi.
              </Typography.Paragraph>
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item name="delivery_price" label="Narxi" extra="0 — bepul">
                    <InputNumber min={0} style={{ width: '100%' }} suffix="so'm" disabled={!delivery} {...moneyInput} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="delivery_days" label="Muddati" extra="Taxminiy yetkazish sanasi shundan hisoblanadi">
                    <InputNumber min={0} max={60} style={{ width: '100%' }} suffix="kun" disabled={!delivery} />
                  </Form.Item>
                </Col>
                <Col span={12}><Form.Item name="delivery_note" label="Izoh"><Input disabled={!delivery} /></Form.Item></Col>
                <Col span={12}><Form.Item name="delivery_note_ru" label="Izoh (ruscha)"><Input disabled={!delivery} /></Form.Item></Col>
              </Row>
            </div>
          </Col>
          <Col xs={24} lg={12}>
            <div className="setting-box">
              <div className="setting-box-head">
                <ShopOutlined /> <b>Do'kondan olib ketish</b>
                <Form.Item name="pickup_enabled" valuePropName="checked" noStyle><Switch /></Form.Item>
              </div>
              <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
                Mijoz buyurtma berishda o'ziga qulay filialni tanlaydi va buyurtmani o'sha yerdan olib ketadi.
                Filiallar darhol saqlanadi.
              </Typography.Paragraph>
              {pickup && activeBranches === 0 && (
                <Alert type="warning" showIcon style={{ marginBottom: 8 }} title="Faol filial yo'q — saytda olib ketish ko'rinmaydi." />
              )}
              <Branches canEdit={canEdit} onChange={onBranches} />
            </div>
          </Col>
        </Row>

        <div className="setting-box" style={{ marginTop: 16 }}>
          <div className="setting-box-head"><PhoneOutlined /> <b>Asosiy aloqa</b></div>
          <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
            Sayt yuqorisida (header) va pastida (footer) ko'rsatiladigan umumiy telefon, manzil va ish vaqti.
          </Typography.Paragraph>
          <Row gutter={12}>
            <Col xs={24} sm={12} lg={6}>
              <Form.Item name="phone" label="Telefon" rules={[{ required: true, message: 'Telefonni kiriting' }]}>
                <Input placeholder="+998 71 000 00 00" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Form.Item name="address" label="Manzil" rules={[{ required: true, message: 'Manzilni kiriting' }]}><Input /></Form.Item>
            </Col>
            <Col xs={24} sm={12} lg={6}><Form.Item name="address_ru" label="Manzil (ruscha)"><Input /></Form.Item></Col>
            <Col xs={24} sm={12} lg={6}>
              <Form.Item name="map_url" label="Xaritadagi havola"><Input placeholder="https://..." /></Form.Item>
            </Col>
            <Col xs={24} sm={12} lg={6}><Form.Item name="working_hours" label="Ish vaqti"><Input /></Form.Item></Col>
            <Col xs={24} sm={12} lg={6}><Form.Item name="working_hours_ru" label="Ish vaqti (ruscha)"><Input /></Form.Item></Col>
          </Row>
        </div>

        {loaded && !delivery && !pickup && (
          <Alert type="error" showIcon style={{ marginTop: 12 }} title="Ikkalasini birdan o'chirib bo'lmaydi — mijozlar buyurtma bera olmay qoladi." />
        )}
      </Form>
    </Card>
  )
}
