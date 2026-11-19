import { useEffect, useMemo, useState } from 'react'
import {
  App, Button, Form, Input, InputNumber, Modal, Popconfirm, Space, Table, Tag, TreeSelect, Typography,
} from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { api, applyFormErrors, errorText } from '../api'
import ImageUpload from '../components/ImageUpload'
import { categoryTree } from './ProductForm'
import { usePerm } from '../auth'

// Sayt kategoriyalarni 3 bosqichgacha ko'rsatadi (backend ham tekshiradi)
const MAX_DEPTH = 3

export default function Categories() {
  const perm = usePerm('categories')
  const { message } = App.useApp()
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null) // null — yopiq, {} — yangi, {...} — tahrirlash
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = () => api('/admin/categories/').then(setList).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  // Jadval uchun daraxt; depth — bosqich (1 dan), height — o'zi va ichkilari nechta bosqich
  const { rows, info } = useMemo(() => {
    const byParent = {}
    const info = {}
    list.forEach(c => { (byParent[c.parent ?? 'root'] ||= []).push(c) })
    const build = (pid, depth) => (byParent[pid] || []).map(c => {
      const children = build(c.id, depth + 1)
      const height = 1 + Math.max(0, ...children.map(ch => info[ch.id].height))
      info[c.id] = { depth, height }
      return { ...c, depth, children: children.length ? children : undefined }
    })
    return { rows: build('root', 1), info }
  }, [list])

  // Kategoriyani o'zining ichiga qo'yib bo'lmaydi; 3 bosqichdan chuqurga tushadigan ota tanlanmaydi
  const parentTree = useMemo(() => {
    const height = editing?.id ? info[editing.id]?.height ?? 1 : 1
    const strip = nodes => nodes.filter(n => n.value !== editing?.id).map(n => ({
      ...n,
      disabled: info[n.value]?.depth + height > MAX_DEPTH,
      children: strip(n.children),
    }))
    return strip(categoryTree(list))
  }, [list, editing, info])

  const open = (cat, parent = null) => {
    setEditing(cat || {})
    form.resetFields()
    form.setFieldsValue(cat || { parent })
  }

  const save = async values => {
    setSaving(true)
    try {
      const body = { ...values, parent: values.parent ?? null }
      const saved = await api(editing.id ? `/admin/categories/${editing.id}/` : '/admin/categories/', {
        method: editing.id ? 'PATCH' : 'POST', body,
      })
      message.success('Saqlandi')
      // Yangi kategoriya yaratilgach ikonka yuklash uchun oyna ochiq qoladi
      if (editing.id) setEditing(null)
      else { setEditing(saved); form.setFieldsValue(saved) }
      load()
    } catch (err) {
      if (!applyFormErrors(form, err)) message.error(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  const remove = async c => {
    try {
      await api(`/admin/categories/${c.id}/`, { method: 'DELETE' })
      message.success('O\'chirildi')
      load()
    } catch (err) {
      message.error(errorText(err))
    }
  }

  // Yangi yozuv — qo'shish, mavjudi — tahrirlash huquqi
  const canSave = editing?.id ? perm.change : perm.add

  return (
    <>
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>Kategoriyalar</Typography.Title>
        {perm.add && <Button type="primary" icon={<PlusOutlined />} onClick={() => open(null)}>Kategoriya qo'shish</Button>}
      </div>

      <Table
        rowKey="id" loading={loading} dataSource={rows} pagination={false} scroll={{ x: 700 }}
        expandable={{ defaultExpandAllRows: true }} key={rows.length}
        columns={[
          {
            title: 'Nomi', dataIndex: 'name',
            render: (n, c) => (
              <Space>
                {c.icon && <img src={c.icon} alt="" className="thumb" style={{ width: 28, height: 28 }} />}
                <b style={{ fontWeight: c.parent ? 400 : 600 }}>{n}</b>
              </Space>
            ),
          },
          { title: 'Mahsulotlar', dataIndex: 'products_count', align: 'center', render: n => <Tag>{n}</Tag> },
          { title: 'Tartib', dataIndex: 'order', align: 'center', width: 80 },
          {
            title: '', key: 'a', width: 170, align: 'right',
            render: (_, c) => (
              <Space>
                {perm.add && c.depth < MAX_DEPTH && (
                  <Button size="small" icon={<PlusOutlined />} title="Ichki kategoriya" onClick={() => open(null, c.id)} />
                )}
                <Button size="small" icon={<EditOutlined />} onClick={() => open(c)} />
                {perm.delete && (
                  <Popconfirm title={`"${c.name}" o'chirilsinmi?`} description="Ichki kategoriyalari ham o'chadi. Ichida mahsulot bo'lsa, o'chirib bo'lmaydi."
                              okText="Ha" cancelText="Yo'q" okButtonProps={{ danger: true }} onConfirm={() => remove(c)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />

      <Modal
        open={editing !== null} title={editing?.id ? 'Kategoriyani tahrirlash' : 'Yangi kategoriya'}
        onCancel={() => setEditing(null)} onOk={() => form.submit()} okText="Saqlash" cancelText="Bekor"
        confirmLoading={saving} destroyOnHidden okButtonProps={{ style: canSave ? undefined : { display: 'none' } }}
      >
        <Form form={form} layout="vertical" onFinish={save} disabled={!canSave}
              onValuesChange={ch => { if ('parent' in ch && !('order' in ch)) form.setFieldValue('order', null) }}>
          <Form.Item name="name" label="Nomi" rules={[{ required: true, message: 'Nomini kiriting' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name_ru" label="Nomi (ruscha)" extra="Bo'sh bo'lsa o'zbekcha nomi ko'rinadi">
            <Input placeholder="Например: Холодильники" />
          </Form.Item>
          <Form.Item name="parent" label="Ota kategoriya" extra={`Kategoriyalar ko'pi bilan ${MAX_DEPTH} bosqich bo'ladi.`}>
            <TreeSelect allowClear treeData={parentTree} treeDefaultExpandAll placeholder="Yo'q (asosiy kategoriya)" />
          </Form.Item>
          <Form.Item name="order" label="Tartib raqami" extra="Shu o'ringa qo'yiladi, qolganlari pastga suriladi. Bo'sh qoldirsangiz oxiriga qo'shiladi.">
            <InputNumber min={1} precision={0} placeholder="Oxiriga" />
          </Form.Item>
          {editing?.id && (
            <Form.Item label="Ikonka">
              <ImageUpload rule="category" path={`/admin/categories/${editing.id}/upload/`} value={editing.icon}
                           onChange={c => { setEditing(c); load() }} label="Ikonka yuklash" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  )
}
