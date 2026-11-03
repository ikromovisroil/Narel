import { useEffect, useState } from 'react'
import { App, Button, Card, Form, Input, Spin, Tabs, Typography } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import { useCanEdit } from '../auth'

// Ommaviy oferta matni — saytdagi kirish oynasida "Ommaviy oferta" havolasi shu sahifani ochadi
export default function OfferCard() {
  const { message } = App.useApp()
  const canEdit = useCanEdit('settings')
  const [form] = Form.useForm()
  const [loaded, setLoaded] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api('/admin/store-settings/').then(s => { form.setFieldsValue({ offer_text: s.offer_text, offer_text_ru: s.offer_text_ru }); setLoaded(true) })
  }, [form])

  const save = async values => {
    setSaving(true)
    try {
      const s = await api('/admin/store-settings/', { method: 'PATCH', body: values })
      form.setFieldsValue({ offer_text: s.offer_text, offer_text_ru: s.offer_text_ru })
      message.success('Oferta saqlandi')
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error({ content: errorText(err), duration: 6 })
    } finally {
      setSaving(false)
    }
  }

  const area = name => <Form.Item name={name} noStyle><Input.TextArea rows={14} placeholder="Oferta matni..." /></Form.Item>

  return (
    <Card
      title={<><FileTextOutlined /> Ommaviy oferta</>} style={{ marginBottom: 16 }}
      extra={canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
    >
      <Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
        Mijoz kirishda "Shartlarga roziman" belgisini qo'yadi; "Ommaviy oferta" havolasi saytdagi /oferta sahifasini ochadi.
        "# " bilan boshlangan qator — bo'lim sarlavhasi (saytda mundarijaga qo'shiladi).
        [Kvadrat qavs] ichidagi joylarni (STIR, bank, manzil va h.k.) kompaniya ma'lumotlari bilan almashtiring.
      </Typography.Paragraph>
      {!loaded ? <Spin /> : (
        <Form form={form} onFinish={save} disabled={!canEdit}>
          <Tabs items={[
            { key: 'uz', label: "O'zbekcha", children: area('offer_text') },
            { key: 'ru', label: 'Ruscha', children: area('offer_text_ru') },
          ]} />
        </Form>
      )}
    </Card>
  )
}
