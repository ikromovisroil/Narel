import { useEffect, useState } from 'react'
import {
  Alert, App, Avatar, Button, Card, Col, Drawer, Form, Input, InputNumber, Row, Space, Spin, Switch, Tag, Typography,
} from 'antd'
import { BookOutlined, CheckCircleFilled, SettingOutlined, WarningFilled } from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import ImageUpload from '../components/ImageUpload'
import PaymentGuide from '../components/PaymentGuide'
import ProviderContacts from '../components/ProviderContacts'
import OfferCard from '../components/OfferCard'
import StoreSettingsCard from '../components/StoreSettingsCard'
import { useCanEdit } from '../auth'

// Logo yuklanmagan bo'lsa — rangli harf
function MethodLogo({ method, size = 44 }) {
  return method.logo
    ? <Avatar shape="square" size={size} src={method.logo} className="method-logo" />
    : (
      <Avatar shape="square" size={size} style={{ background: COLORS[method.code], fontWeight: 700 }}>
        {method.title[0]}
      </Avatar>
    )
}

const COLORS = {
  cash: '#17a34a', card: '#1f5eff', click: '#0096e0', payme: '#00c2c7',
  paynet: '#00a651', uzum: '#7b2cbf', installment: '#ff6a00',
}

function MethodDrawer({ method, onClose, onSaved }) {
  const canEdit = useCanEdit('settings')
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (method) {
      form.resetFields()
      form.setFieldsValue({ ...method, config: { ...method.config } })
    }
  }, [method, form])

  const save = async values => {
    setSaving(true)
    try {
      const saved = await api(`/admin/payment-methods/${method.id}/`, { method: 'PATCH', body: values })
      message.success('Saqlandi')
      onSaved(saved)
      onClose()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Drawer
      open={Boolean(method)} onClose={onClose} size={520}
      title={method && <Space><MethodLogo method={method} size={32} />{method.title}</Space>}
      extra={canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      {method && (
        <Form form={form} layout="vertical" onFinish={save} requiredMark={false} disabled={!canEdit}>
          {method.about && <Alert type="info" showIcon title={method.about} style={{ marginBottom: 16 }} />}
          {method.where.length > 0 && (
            <div className="where-box">
              <b>Kalitlar qayerdan olinadi</b>
              <ol>{method.where.map(w => <li key={w}>{w}</li>)}</ol>
            </div>
          )}
          <ProviderContacts contacts={method.contacts} />
          <Typography.Title level={5} style={{ marginTop: 0 }}>Saytda ko'rinishi</Typography.Title>
          <Form.Item label="Logo" extra="Buyurtma sahifasida nom yonida ko'rinadi">
            <ImageUpload rule="payment_logo" path={`/admin/payment-methods/${method.id}/upload/`} value={method.logo}
                         onChange={saved => onSaved(saved, true)} label="Logo yuklash" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="title" label="Nomi" rules={[{ required: true, message: 'Nomini kiriting' }]}
                         extra="Mijoz buyurtma sahifasida ko'radigan nom"><Input /></Form.Item>
            </Col>
            <Col span={12}><Form.Item name="title_ru" label="Nomi (ruscha)" extra="Bo'sh bo'lsa o'zbekchasi"><Input /></Form.Item></Col>
            <Col span={12}>
              <Form.Item name="description" label="Izoh" extra="Nom ostidagi kichik matn"><Input /></Form.Item>
            </Col>
            <Col span={12}><Form.Item name="description_ru" label="Izoh (ruscha)"><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="order" label="Tartib raqami" extra="Buyurtma sahifasida shu tartibda ko'rsatiladi">
            <InputNumber min={0} />
          </Form.Item>

          {method.fields_schema.length > 0 && (
            <>
              <Typography.Title level={5}>Ulanish ma'lumotlari</Typography.Title>
              <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
                Bu ma'lumotlar to'lov tizimi bilan shartnoma tuzilgandan keyin beriladi.
                Maxfiy kalitlar saytga va boshqa joyga hech qachon chiqmaydi.
              </Typography.Paragraph>
              {method.fields_schema.map(f => (
                <Form.Item
                  key={f.key} name={['config', f.key]}
                  label={<Space size={6}>{f.label}{f.required && <Tag color="red" style={{ marginInlineEnd: 0 }}>majburiy</Tag>}</Space>}
                  extra={f.secret && f.is_set ? `${f.hint}. Kiritilgan — o'zgartirmaslik uchun bo'sh qoldiring.` : f.hint}
                >
                  {f.secret
                    ? <Input.Password placeholder={f.is_set ? '••••••••' : ''} autoComplete="new-password" />
                    : <Input />}
                </Form.Item>
              ))}
              <Form.Item name="test_mode" label="Sinov rejimi" valuePropName="checked"
                         extra="Yoqilgan bo'lsa to'lov tizimining sinov (sandbox) muhitidan foydalaniladi">
                <Switch />
              </Form.Item>
            </>
          )}
        </Form>
      )}
    </Drawer>
  )
}

export default function Settings() {
  const canEdit = useCanEdit('settings')
  const { message } = App.useApp()
  const [methods, setMethods] = useState(null)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(null)
  const [guide, setGuide] = useState(false)

  const load = () => api('/admin/payment-methods/').then(setMethods)
  useEffect(() => { load() }, [])

  const replace = saved => setMethods(list => list.map(m => (m.id === saved.id ? saved : m)))

  const toggle = async (m, is_active) => {
    setBusy(m.id)
    try {
      replace(await api(`/admin/payment-methods/${m.id}/`, { method: 'PATCH', body: { is_active } }))
      message.success(`${m.title}: ${is_active ? 'yoqildi' : 'o\'chirildi'}`)
    } catch (err) {
      message.error({ content: errorText(err), duration: 6 })
      if (is_active && !m.is_configured) setEditing(m)
    } finally {
      setBusy(null)
    }
  }

  if (!methods) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

  const activeCount = methods.filter(m => m.is_active).length

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Sozlamalar</Typography.Title>
        <Button icon={<BookOutlined />} onClick={() => setGuide(true)}>Qo'llanma</Button>
      </div>

      <StoreSettingsCard />
      <OfferCard />

      <Card title="To'lov usullari" extra={<Typography.Text type="secondary">{activeCount} ta yoqilgan</Typography.Text>}>
        <Alert
          type="info" showIcon style={{ marginBottom: 16 }}
          title="Qanday ishlaydi"
          description={
            <ul className="guide-list compact">
              <li>Tugma <b>yoqiq</b> bo'lsa — usul saytdagi buyurtma sahifasida chiqadi. <b>O'chiq</b> bo'lsa — chiqmaydi va u bilan buyurtma berib bo'lmaydi.</li>
              <li>Naqd va kuryerga karta — kalitsiz, darhol yoqiladi. Onlayn usullar va nasiya — avval <b>"Sozlash"</b> orqali kalitlarni kiriting.</li>
              <li>Muddatli to'lov o'chiq bo'lsa, saytda "× N oy" narxlari ko'rinmaydi.</li>
            </ul>
          }
          action={<Button size="small" type="link" onClick={() => setGuide(true)}>To'liq qo'llanma</Button>}
        />
        {activeCount === 0 && (
          <Alert type="error" showIcon style={{ marginBottom: 16 }}
                 title="Hech qanday to'lov usuli yoqilmagan — mijozlar buyurtma bera olmaydi." />
        )}

        <Row gutter={[16, 16]}>
          {methods.map(m => (
            <Col xs={24} md={12} xl={8} key={m.id}>
              <Card size="small" className={`pay-card ${m.is_active ? 'on' : ''}`}>
                <div className="pay-card-head">
                  <MethodLogo method={m} />
                  <div className="pay-card-title">
                    <b>{m.title}</b>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>{m.description}</Typography.Text>
                  </div>
                  <Switch checked={m.is_active} loading={busy === m.id} disabled={!canEdit} onChange={v => toggle(m, v)} />
                </div>
                <div className="pay-card-foot">
                  {m.fields_schema.length === 0 ? (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>Kalit talab qilinmaydi</Typography.Text>
                  ) : m.is_configured ? (
                    <Typography.Text type="success" style={{ fontSize: 12 }}>
                      <CheckCircleFilled /> Sozlangan{m.test_mode && <Tag color="orange" style={{ marginLeft: 8 }}>sinov rejimi</Tag>}
                    </Typography.Text>
                  ) : (
                    <Typography.Text type="warning" style={{ fontSize: 12 }}>
                      <WarningFilled /> Sozlanmagan
                    </Typography.Text>
                  )}
                  <Button size="small" icon={<SettingOutlined />} onClick={() => setEditing(m)}>Sozlash</Button>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <MethodDrawer
        method={editing} onClose={() => setEditing(null)}
        onSaved={(saved, keepOpen) => { replace(saved); if (keepOpen) setEditing(saved) }}
      />
      <PaymentGuide open={guide} onClose={() => setGuide(false)} methods={methods} />
    </>
  )
}
