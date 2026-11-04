import { useEffect, useState } from 'react'
import {
  Alert, App, Avatar, Button, Card, Col, Drawer, Form, Input, InputNumber, Row, Space, Spin, Switch, Tag, Typography,
} from 'antd'
import {
  CheckCircleFilled, CloseCircleFilled, GoogleOutlined, MessageOutlined, SendOutlined, SettingOutlined,
  SyncOutlined, WarningFilled,
} from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import { useCanEdit } from '../auth'
import { formatNumber } from '../utils'
import ProviderContacts from './ProviderContacts'

const SMS_STATUS = {
  sent: { color: 'green', label: 'Yuborildi' },
  failed: { color: 'red', label: 'Xato' },
  test: { color: 'default', label: 'Test' },
}

// SMS holati: kartada va oynada bir xil ko'rinadi
export function SmsState({ data }) {
  const s = data.sms
  if (!s.enabled) return <Typography.Text type="secondary"><CloseCircleFilled /> O'chirilgan</Typography.Text>
  if (s.mode === 'test') {
    return <Typography.Text type="warning"><WarningFilled /> Sozlanmagan — test rejimi (kod ekranga chiqadi)</Typography.Text>
  }
  if (s.mode === 'off') return <Typography.Text type="danger"><WarningFilled /> Sozlanmagan — mijozlar kira olmaydi</Typography.Text>
  if (s.unreachable) {
    return <Typography.Text type="danger"><WarningFilled /> Eskiz'ga ulanib bo'lmadi{s.error && `: ${s.error}`}</Typography.Text>
  }
  return (
    <Typography.Text type={s.low ? 'warning' : 'success'}>
      {s.low ? <WarningFilled /> : <CheckCircleFilled />} Ishlayapti · balans {formatNumber(s.balance)}
      {s.low && ' — kam qoldi, to\'ldiring'}
    </Typography.Text>
  )
}

function Guide({ guide }) {
  return (
    <>
      <Alert type="info" showIcon title={guide.about} style={{ marginBottom: 16 }} />
      <div className="where-box">
        <b>Qanday ulanadi</b>
        <ol>{guide.where.map(w => <li key={w}>{w}</li>)}</ol>
      </div>
      <ProviderContacts contacts={guide.contacts} />
    </>
  )
}

function useSave(form, onSaved, onClose) {
  const { message } = App.useApp()
  const [saving, setSaving] = useState(false)
  const save = async values => {
    setSaving(true)
    try {
      onSaved(await api('/admin/integrations/', { method: 'PATCH', body: values }))
      message.success('Saqlandi')
      onClose?.()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error({ content: errorText(err), duration: 6 })
    } finally {
      setSaving(false)
    }
  }
  return [save, saving]
}

function SmsDrawer({ open, data, onClose, onSaved }) {
  const canEdit = useCanEdit('settings')
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [save, saving] = useSave(form, d => { onSaved(d); form.setFieldValue('eskiz_password', '') })
  const [checking, setChecking] = useState(false)
  const [phone, setPhone] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    if (open) {
      form.resetFields()
      form.setFieldsValue({ ...data, eskiz_password: '' })
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  const check = async () => {
    setChecking(true)
    try {
      const r = await api('/admin/integrations/sms-check/', { method: 'POST' })
      onSaved({ ...data, sms: r.sms })
      message.success(`Ulanish to'g'ri. Balans: ${formatNumber(r.balance)}`)
    } catch (err) {
      message.error({ content: errorText(err), duration: 8 })
    } finally {
      setChecking(false)
    }
  }

  const sendTest = async () => {
    setSending(true)
    try {
      const r = await api('/admin/integrations/sms-test/', { method: 'POST', body: { phone } })
      message.success({ content: r.detail, duration: 6 })
    } catch (err) {
      message.error({ content: errorText(err), duration: 8 })
    } finally {
      setSending(false)
      onSaved(await api('/admin/integrations/'))
    }
  }

  const usingEnv = data.env.eskiz && !data.eskiz_email
  const guide = data.guides.sms

  return (
    <Drawer
      open={open} onClose={onClose} size={600}
      title={<Space><Avatar shape="square" icon={<MessageOutlined />} style={{ background: '#1f5eff' }} />{guide.title}</Space>}
      extra={canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      <div style={{ marginBottom: 16 }}><SmsState data={data} /></div>
      <Guide guide={guide} />

      <Typography.Title level={5}>Moderatsiyaga beriladigan matnlar</Typography.Title>
      <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
        Eskiz kabinetida aynan shu matnlarni shablon qilib yuboring (123456 — kod o'rni). Domen o'zgarsa matn ham o'zgaradi.
      </Typography.Paragraph>
      {data.sms_templates.map(t => (
        <Typography.Paragraph key={t.lang} copyable={{ text: t.text, tooltips: ['Nusxa olish', 'Nusxa olindi'] }}
                              className="sms-template">
          <Tag>{t.lang}</Tag><span style={{ whiteSpace: 'pre-wrap' }}>{t.text}</span>
        </Typography.Paragraph>
      ))}

      <Typography.Title level={5}>Ulanish ma'lumotlari</Typography.Title>
      {usingEnv && (
        <Alert type="info" showIcon style={{ marginBottom: 12 }}
               title="Hozir serverdagi .env fayldagi kalitlar ishlatilmoqda. Shu yerga kiritsangiz, ular ustun bo'ladi." />
      )}
      <Form form={form} layout="vertical" onFinish={save} requiredMark={false} disabled={!canEdit}>
        <Form.Item name="sms_enabled" label="SMS yuborish" valuePropName="checked"
                   extra="O'chirilsa mijozlar telefon orqali kira olmaydi (faqat Google orqali)">
          <Switch checkedChildren="yoqiq" unCheckedChildren="o'chiq" />
        </Form.Item>
        <Row gutter={12}>
          <Col xs={24} sm={12}>
            <Form.Item name="eskiz_email" label="Login (email)" extra="my.eskiz.uz ga kiradigan email">
              <Input autoComplete="off" placeholder="shop@narel.uz" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="eskiz_password" label="Parol yoki maxfiy kalit"
                       extra={data.has_password ? "Kiritilgan. O'zgartirmaslik uchun bo'sh qoldiring." : 'Hech qayerda ko\'rinmaydi'}>
              <Input.Password autoComplete="new-password" placeholder={data.has_password ? '••••••••' : ''} />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="eskiz_from" label="Jo'natuvchi nomi"
                       extra={`Bo'sh bo'lsa "${data.sms_sender}". "Narel" nomi Eskiz'da ro'yxatdan o'tgach yoziladi`}>
              <Input placeholder="4546" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="sms_low_balance" label="Balans ogohlantirishi"
                       extra={`Balans shundan kam bo'lsa bosh sahifada ogohlantirish chiqadi (hozir ${formatNumber(data.sms.threshold)})`}>
              <InputNumber min={0} style={{ width: '100%' }} placeholder={String(data.sms.threshold)} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="sms_otp_domain" label="Kodni avtomatik to'ldirish (Android)"
                   extra="Sayt domeni, masalan narel.uz. SMS oxiriga maxsus qator qo'shiladi va Android'da kod maydonga o'zi tushadi. Bo'sh — o'chiq.">
          <Input placeholder="narel.uz" />
        </Form.Item>
      </Form>

      <Typography.Title level={5}>Tekshirish</Typography.Title>
      <Space wrap style={{ marginBottom: 8 }}>
        <Button icon={<SyncOutlined />} loading={checking} onClick={check} disabled={!canEdit || data.sms.mode !== 'live'}>
          Ulanishni tekshirish
        </Button>
        <Space.Compact>
          <Input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+998 90 123 45 67"
                 style={{ width: 190 }} disabled={!canEdit} />
          <Button icon={<SendOutlined />} loading={sending} onClick={sendTest} disabled={!canEdit || !phone}>
            Sinov SMS
          </Button>
        </Space.Compact>
      </Space>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
        Avval saqlang, keyin tekshiring. Sinov SMS kirish kodi matni bilan ketadi va balansdan yechiladi.
      </Typography.Paragraph>

      <Typography.Title level={5}>Oxirgi SMS'lar</Typography.Title>
      {data.recent_sms.length === 0 ? (
        <Typography.Text type="secondary">Hali SMS yuborilmagan</Typography.Text>
      ) : (
        <div className="sms-log">
          {data.recent_sms.map(s => (
            <div key={s.id} className="sms-log-row">
              <Tag color={SMS_STATUS[s.status]?.color}>{SMS_STATUS[s.status]?.label}</Tag>
              <span>{s.phone}</span>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {new Date(s.created_at).toLocaleString('uz-UZ')}
              </Typography.Text>
              {s.error && <Typography.Text type="danger" style={{ fontSize: 12, flexBasis: '100%' }}>{s.error}</Typography.Text>}
            </div>
          ))}
        </div>
      )}
    </Drawer>
  )
}

function GoogleDrawer({ open, data, onClose, onSaved }) {
  const canEdit = useCanEdit('settings')
  const [form] = Form.useForm()
  const [save, saving] = useSave(form, onSaved, onClose)

  useEffect(() => {
    if (open) {
      form.resetFields()
      form.setFieldsValue({
        google_client_id: data.google_client_id,
        google_ios_client_id: data.google_ios_client_id,
        google_android_client_id: data.google_android_client_id,
      })
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  const guide = data.guides.google
  return (
    <Drawer
      open={open} onClose={onClose} size={560}
      title={<Space><Avatar shape="square" icon={<GoogleOutlined />} style={{ background: '#ea4335' }} />{guide.title}</Space>}
      extra={canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      <Guide guide={guide} />
      {data.env.google && !data.google_client_id && (
        <Alert type="info" showIcon style={{ marginBottom: 12 }}
               title="Hozir serverdagi .env fayldagi Client ID ishlatilmoqda. Shu yerga kiritsangiz, u ustun bo'ladi." />
      )}
      <Form form={form} layout="vertical" onFinish={save} requiredMark={false} disabled={!canEdit}>
        <Form.Item name="google_client_id" label="Client ID (sayt)"
                   extra="Turi &quot;Web application&quot;. Bo'sh qoldirilsa saytda &quot;Google orqali kirish&quot; tugmasi ko'rinmaydi">
          <Input placeholder="1234567890-abc.apps.googleusercontent.com" />
        </Form.Item>
        <Typography.Title level={5}>Mobil ilovalar</Typography.Title>
        <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
          Faqat iOS yoki Android ilova bo'lsa kerak. Ilova o'zining Client ID'si bilan kiradi — shu yerga qo'shilmasa, ilovadan Google orqali kirish rad etiladi.
        </Typography.Paragraph>
        <Row gutter={12}>
          <Col xs={24} sm={12}>
            <Form.Item name="google_ios_client_id" label="iOS Client ID" extra="Turi &quot;iOS&quot;">
              <Input placeholder="…apps.googleusercontent.com" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="google_android_client_id" label="Android Client ID" extra="Turi &quot;Android&quot; (paket nomi va SHA-1 bilan)">
              <Input placeholder="…apps.googleusercontent.com" />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Drawer>
  )
}

export default function IntegrationsCard() {
  const [data, setData] = useState(null)
  const [open, setOpen] = useState(null) // 'sms' | 'google'

  useEffect(() => { api('/admin/integrations/').then(setData) }, [])

  const googleOn = data && (data.google_client_id || data.env.google)

  return (
    <Card title="Integratsiyalar" extra={<Typography.Text type="secondary">SMS va Google orqali kirish</Typography.Text>}>
      {!data ? <Spin style={{ display: 'block', margin: '24px auto' }} /> : (
        <>
          {data.sms.mode === 'off' && !googleOn && (
            <Alert type="error" showIcon style={{ marginBottom: 16 }}
                   title="Na SMS, na Google sozlangan — mijozlar saytga kira olmaydi va buyurtma bera olmaydi." />
          )}
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small" className={`pay-card ${data.sms.mode === 'live' ? 'on' : ''}`}>
                <div className="pay-card-head">
                  <Avatar shape="square" size={44} icon={<MessageOutlined />} style={{ background: '#1f5eff' }} />
                  <div className="pay-card-title">
                    <b>SMS kod (Eskiz.uz)</b>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>Telefon raqami bilan kirish</Typography.Text>
                  </div>
                </div>
                <div className="pay-card-foot">
                  <span style={{ fontSize: 12 }}><SmsState data={data} /></span>
                  <Button size="small" icon={<SettingOutlined />} onClick={() => setOpen('sms')}>Sozlash</Button>
                </div>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card size="small" className={`pay-card ${googleOn ? 'on' : ''}`}>
                <div className="pay-card-head">
                  <Avatar shape="square" size={44} icon={<GoogleOutlined />} style={{ background: '#ea4335' }} />
                  <div className="pay-card-title">
                    <b>Google orqali kirish</b>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>Google hisobi bilan bir tugmada</Typography.Text>
                  </div>
                </div>
                <div className="pay-card-foot">
                  {googleOn ? (
                    <Typography.Text type="success" style={{ fontSize: 12 }}><CheckCircleFilled /> Sozlangan</Typography.Text>
                  ) : (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>Sozlanmagan — tugma saytda ko'rinmaydi</Typography.Text>
                  )}
                  <Button size="small" icon={<SettingOutlined />} onClick={() => setOpen('google')}>Sozlash</Button>
                </div>
              </Card>
            </Col>
          </Row>
          <SmsDrawer open={open === 'sms'} data={data} onClose={() => setOpen(null)} onSaved={setData} />
          <GoogleDrawer open={open === 'google'} data={data} onClose={() => setOpen(null)} onSaved={setData} />
        </>
      )}
    </Card>
  )
}
