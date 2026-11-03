import { useEffect, useState } from 'react'
import {
  App, Button, Card, Col, Empty, Form, Input, InputNumber, Modal, Popconfirm, Row, Space, Switch, Tag, Typography,
} from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import ImageUpload from '../components/ImageUpload'
import { usePerm } from '../auth'

const GRADIENTS = [
  'linear-gradient(120deg, #1f5eff, #6b3bff)',
  'linear-gradient(120deg, #ff6a00, #ff2f6d)',
  'linear-gradient(120deg, #0f9b8e, #1f5eff)',
]

export default function Banners() {
  const perm = usePerm('banners')
  const { message } = App.useApp()
  const [list, setList] = useState(null)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = () => api('/admin/banners/').then(setList)
  useEffect(() => { load() }, [])

  const open = b => {
    setEditing(b || {})
    form.resetFields()
    form.setFieldsValue(b || { is_active: true })
  }

  const save = async values => {
    setSaving(true)
    try {
      const saved = await api(editing.id ? `/admin/banners/${editing.id}/` : '/admin/banners/', {
        method: editing.id ? 'PATCH' : 'POST', body: values,
      })
      message.success('Saqlandi')
      if (editing.id) setEditing(null)
      else { setEditing(saved); form.setFieldsValue(saved) }
      load()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  const patch = async (b, body) => {
    await api(`/admin/banners/${b.id}/`, { method: 'PATCH', body }).catch(err => message.error(errorText(err)))
    load()
  }

  const remove = async b => {
    await api(`/admin/banners/${b.id}/`, { method: 'DELETE' }).catch(err => message.error(errorText(err)))
    load()
  }

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Bannerlar</Typography.Title>
        {perm.add && <Button type="primary" icon={<PlusOutlined />} onClick={() => open(null)}>Banner qo'shish</Button>}
      </div>
      <Typography.Paragraph type="secondary">
        Bannerlar sayt bosh sahifasidagi slayderda tartib raqami bo'yicha ko'rsatiladi. Rasm yuklanmasa rangli fon ishlatiladi.
      </Typography.Paragraph>

      {list && !list.length && <Empty description="Banner yo'q" />}
      <Row gutter={[16, 16]}>
        {(list || []).map((b, i) => (
          <Col xs={24} md={12} xl={8} key={b.id}>
            <Card
              cover={
                <div style={{
                  height: 150, padding: 20, color: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'center',
                  background: b.image ? `center/cover url(${b.image})` : GRADIENTS[i % 3], opacity: b.is_active ? 1 : 0.4,
                }}>
                  <b style={{ fontSize: 18 }}>{b.title}</b>
                  <span style={{ opacity: 0.9 }}>{b.subtitle}</span>
                </div>
              }
              actions={[
                perm.change && <Switch key="s" size="small" checked={b.is_active} onChange={v => patch(b, { is_active: v })} />,
                perm.change && <EditOutlined key="e" onClick={() => open(b)} />,
                perm.delete && <Popconfirm key="d" title="Banner o'chirilsinmi?" okText="Ha" cancelText="Yo'q" onConfirm={() => remove(b)}>
                  <DeleteOutlined style={{ color: '#e5383b' }} />
                </Popconfirm>,
              ].filter(Boolean)}
            >
              <Space>
                <Tag>Tartib: {b.order}</Tag>
                {b.link && <Typography.Text type="secondary" ellipsis style={{ maxWidth: 180 }}>{b.link}</Typography.Text>}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        open={editing !== null} title={editing?.id ? 'Bannerni tahrirlash' : 'Yangi banner'}
        onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Saqlash" cancelText="Yopish"
        confirmLoading={saving} destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={save} disabled={!(editing?.id ? perm.change : perm.add)}>
          <Form.Item name="title" label="Sarlavha" rules={[{ required: true, message: 'Sarlavhani kiriting' }]}><Input /></Form.Item>
          <Form.Item name="subtitle" label="Qo'shimcha matn"><Input /></Form.Item>
          <Form.Item name="title_ru" label="Sarlavha (ruscha)"><Input /></Form.Item>
          <Form.Item name="subtitle_ru" label="Qo'shimcha matn (ruscha)" extra="Bo'sh bo'lsa o'zbekcha matn ko'rinadi">
            <Input />
          </Form.Item>
          <Form.Item name="link" label="Havola" extra="Masalan: /catalog?discount=true yoki /catalog/smartfonlar">
            <Input />
          </Form.Item>
          <Space size="large">
            <Form.Item name="order" label="Tartib" tooltip="Shu o'ringa qo'yiladi, qolganlari suriladi. Bo'sh bo'lsa oxiriga.">
              <InputNumber min={1} precision={0} placeholder="Oxiriga" />
            </Form.Item>
            <Form.Item name="is_active" label="Faol" valuePropName="checked"><Switch /></Form.Item>
          </Space>
          <Form.Item label="Rasm" extra={!editing?.id && 'Rasmni banner saqlangandan keyin yuklaysiz'}>
            {editing?.id && (
              <ImageUpload rule="banner" path={`/admin/banners/${editing.id}/upload/`} value={editing.image}
                           onChange={b => { setEditing(b); load() }} />
            )}
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
