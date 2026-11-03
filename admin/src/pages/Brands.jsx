import { useEffect, useState } from 'react'
import { App, Button, Form, Input, Modal, Popconfirm, Space, Table, Tag, Typography } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { api, applyFormErrors, errorText } from '../api'
import ImageUpload from '../components/ImageUpload'

export default function Brands() {
  const { message } = App.useApp()
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [search, setSearch] = useState('')
  const [form] = Form.useForm()

  const load = () => api('/admin/brands/').then(setList).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const open = b => {
    setEditing(b || {})
    form.resetFields()
    form.setFieldsValue(b || {})
  }

  const save = async values => {
    setSaving(true)
    try {
      const saved = await api(editing.id ? `/admin/brands/${editing.id}/` : '/admin/brands/', {
        method: editing.id ? 'PATCH' : 'POST', body: values,
      })
      message.success('Saqlandi')
      // Yangi brend yaratilgach logotip yuklash uchun oyna ochiq qoladi
      if (editing.id) setEditing(null)
      else { setEditing(saved); form.setFieldsValue(saved) }
      load()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  const remove = async b => {
    try {
      await api(`/admin/brands/${b.id}/`, { method: 'DELETE' })
      message.success('O\'chirildi')
      load()
    } catch (err) {
      message.error(errorText(err))
    }
  }

  const rows = list.filter(b => b.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Brendlar</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => open(null)}>Brend qo'shish</Button>
      </div>
      <div className="toolbar">
        <Input.Search placeholder="Qidirish" allowClear style={{ width: 240 }} onChange={e => setSearch(e.target.value)} />
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={rows} pagination={false}
        columns={[
          {
            title: 'Logo', dataIndex: 'logo', width: 80,
            render: l => (l ? <img src={l} alt="" className="thumb" /> : <div className="thumb">—</div>),
          },
          { title: 'Nomi', dataIndex: 'name', render: n => <b>{n}</b> },
          { title: 'Slug', dataIndex: 'slug', responsive: ['md'] },
          {
            title: 'Mahsulotlar', dataIndex: 'products_count', align: 'center',
            render: (n, b) => <Link to={`/products?brand=${b.id}`}><Tag>{n}</Tag></Link>,
          },
          {
            title: '', key: 'a', width: 110, align: 'right',
            render: (_, b) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => open(b)} />
                <Popconfirm title={`"${b.name}" o'chirilsinmi?`} description="Mahsulotlardan brend olib tashlanadi."
                            okText="Ha" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(b)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        open={editing !== null} title={editing?.id ? 'Brendni tahrirlash' : 'Yangi brend'}
        onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Saqlash" cancelText="Yopish"
        confirmLoading={saving} destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={save}>
          <Form.Item name="name" label="Nomi" rules={[{ required: true, message: 'Nomini kiriting' }]}><Input /></Form.Item>
          <Form.Item name="slug" label="Slug" extra="Bo'sh qoldirsangiz avtomatik yasaladi"><Input /></Form.Item>
          <Form.Item label="Logo" extra={!editing?.id && 'Logoni brend saqlangandan keyin yuklaysiz'}>
            {editing?.id && (
              <ImageUpload path={`/admin/brands/${editing.id}/upload/`} value={editing.logo}
                           onChange={b => { setEditing(b); load() }} label="Logo yuklash" />
            )}
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
