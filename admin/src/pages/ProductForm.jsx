import { useEffect, useMemo, useState } from 'react'
import {
  Alert, App, Breadcrumb, Button, Card, Col, Form, Input, InputNumber, Popconfirm, Row, Select, Space,
  Spin, Switch, TreeSelect, Typography, Upload,
} from 'antd'
import { DeleteOutlined, HolderOutlined, PlusOutlined } from '@ant-design/icons'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, applyFormErrors, errorText, upload } from '../api'
import ImageUpload from '../components/ImageUpload'
import { acceptFor, checkImage, useImageRule } from '../imageRules'
import { formatPrice, moneyInput } from '../utils'
import { usePerm } from '../auth'

export function categoryTree(list) {
  const byParent = {}
  list.forEach(c => { (byParent[c.parent ?? 'root'] ||= []).push(c) })
  const build = pid => (byParent[pid] || []).map(c => ({
    value: c.id, title: c.name, key: c.id, children: build(c.id),
  }))
  return build('root')
}

function Gallery({ product, onChange }) {
  const { message } = App.useApp()
  const rule = useImageRule('product')
  const [busy, setBusy] = useState(false)

  const add = async file => {
    const problem = await checkImage(file, rule)
    if (problem) {
      message.error({ content: `${file.name}: ${problem}`, duration: 6 })
      return Upload.LIST_IGNORE
    }
    setBusy(true)
    try {
      onChange(await upload(`/admin/products/${product.id}/images/`, file))
    } catch (err) {
      message.error({ content: `${file.name}: ${errorText(err)}`, duration: 6 })
    } finally {
      setBusy(false)
    }
    return false
  }
  const remove = async img => {
    try {
      await api(`/admin/product-images/${img.id}/`, { method: 'DELETE' })
      onChange({ ...product, images: product.images.filter(i => i.id !== img.id) })
    } catch (err) {
      message.error(errorText(err))
    }
  }

  return (
    <>
    <div className="gallery">
      {product.images.map(img => (
        <div key={img.id} className="gallery-item">
          <img src={img.image} alt="" />
          <Popconfirm title="Rasmni o'chirasizmi?" okText="Ha" cancelText="Yo'q" onConfirm={() => remove(img)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ))}
      <Upload accept={acceptFor(rule)} multiple showUploadList={false} beforeUpload={add} disabled={busy}>
        <button type="button" className="gallery-item" style={{ cursor: 'pointer', display: 'grid', placeItems: 'center', border: '1px dashed #bbb' }}>
          {busy ? <Spin size="small" /> : <span><PlusOutlined /><div style={{ fontSize: 12 }}>Qo'shish</div></span>}
        </button>
      </Upload>
    </div>
    {rule && (
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, margin: '6px 0 0' }}>
        Asosiy rasm bilan bir xil talablar. Mahsulotni turli tomondan ko'rsating.
      </Typography.Paragraph>
    )}
    </>
  )
}

export default function ProductForm() {
  const perm = usePerm('products')
  const { id } = useParams()
  const isNew = !id
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [product, setProduct] = useState(null)
  const [categories, setCategories] = useState([])
  const [brands, setBrands] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const price = Number(Form.useWatch('price', form)) || 0
  const oldPrice = Number(Form.useWatch('old_price', form)) || 0

  useEffect(() => {
    api('/admin/categories/').then(setCategories)
    api('/admin/brands/').then(setBrands)
  }, [])

  useEffect(() => {
    if (isNew) {
      setProduct(null)
      form.resetFields()
      return
    }
    api(`/admin/products/${id}/`).then(p => {
      setProduct(p)
      form.setFieldsValue(p)
    }).catch(() => message.error('Mahsulot topilmadi'))
  }, [id, isNew, form, message])

  const tree = useMemo(() => categoryTree(categories), [categories])

  const save = async values => {
    setSaving(true); setError('')
    const body = { ...values, old_price: values.old_price || null, brand: values.brand ?? null }
    try {
      const p = await api(isNew ? '/admin/products/' : `/admin/products/${id}/`, {
        method: isNew ? 'POST' : 'PATCH', body,
      })
      message.success(isNew ? 'Mahsulot qo\'shildi. Endi rasmlarini yuklang.' : 'Saqlandi')
      if (isNew) navigate(`/products/${p.id}`, { replace: true })
      else { setProduct(p); form.setFieldsValue(p) }
    } catch (err) {
      if (!applyFormErrors(form, err)) setError(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  // Yangi mahsulot — qo'shish huquqi, mavjudi — tahrirlash huquqi kerak
  const canEdit = isNew ? perm.add : perm.change

  if (!isNew && !product) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

  const discount = price && oldPrice > price ? Math.round((oldPrice - price) * 100 / oldPrice) : 0

  return (
    <>
      <Breadcrumb style={{ marginBottom: 8 }} items={[
        { title: <Link to="/products">Mahsulotlar</Link> },
        { title: isNew ? 'Yangi mahsulot' : product.name },
      ]} />
      <div className="page-head">
        <Typography.Title level={3} style={{ margin: 0 }}>{isNew ? 'Yangi mahsulot' : product.name}</Typography.Title>
        <Space>
          {!isNew && <Button href={`http://localhost:5173/product/${product.slug}`} target="_blank">Saytda ko'rish ↗</Button>}
          {canEdit && <Button type="primary" loading={saving} onClick={() => form.submit()}>Saqlash</Button>}
        </Space>
      </div>

      <Form
        form={form} layout="vertical" onFinish={save} scrollToFirstError disabled={!canEdit}
        initialValues={{ is_active: true, is_hit: false, is_new: true, stock: 0, specs: [] }}
      >
        <Row gutter={16}>
          <Col xs={24} lg={16}>
            <Card title="Asosiy ma'lumotlar" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item name="name" label="Nomi" rules={[{ required: true, message: 'Nomini kiriting' }]}>
                    <Input placeholder="Masalan: Samsung Galaxy A56 8/256GB" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="sku" label="Mahsulot kodi"><Input placeholder="Masalan: SM-A566B" /></Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item name="category" label="Kategoriya" rules={[{ required: true, message: 'Kategoriyani tanlang' }]}>
                    <TreeSelect treeData={tree} treeDefaultExpandAll showSearch treeNodeFilterProp="title"
                                placeholder="Tanlang" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="brand" label="Brend">
                    <Select allowClear showSearch optionFilterProp="label" placeholder="Tanlang"
                            options={brands.map(b => ({ value: b.id, label: b.name }))} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="description" label="Tavsif">
                <Input.TextArea rows={5} />
              </Form.Item>
            </Card>

            <Card
              title="Ruscha tarjima"
              extra={<Typography.Text type="secondary" style={{ fontSize: 12 }}>Ixtiyoriy</Typography.Text>}
              style={{ marginBottom: 16 }}
            >
              <Form.Item name="name_ru" label="Nomi (ruscha)"
                         extra="Bo'sh bo'lsa saytning ruscha versiyasida o'zbekcha nomi ko'rinadi">
                <Input placeholder="Например: Холодильник Samsung RB38" />
              </Form.Item>
              <Form.Item name="description_ru" label="Tavsif (ruscha)" style={{ marginBottom: 0 }}>
                <Input.TextArea rows={4} />
              </Form.Item>
            </Card>

            <Card title="Xususiyatlar" style={{ marginBottom: 16 }}>
              <Form.List name="specs">
                {(fields, { add, remove, move }) => (
                  <>
                    {fields.length > 0 && (
                      <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                        Yuqori qator — o'zbekcha, pastki — ruscha (ixtiyoriy).
                      </Typography.Text>
                    )}
                    {fields.map(({ key, name }, i) => (
                      <Row key={key} gutter={8} align="middle" wrap={false} style={{ marginBottom: 12 }}>
                        <Col flex="none"><HolderOutlined style={{ color: '#bbb' }} /></Col>
                        <Col flex="1">
                          <div className="spec-grid">
                            <Form.Item name={[name, 'name']} noStyle rules={[{ required: true, message: 'Nomi' }]}>
                              <Input prefix={<span className="lang-tag">UZ</span>} placeholder="Masalan: Ekran" />
                            </Form.Item>
                            <Form.Item name={[name, 'value']} noStyle rules={[{ required: true, message: 'Qiymati' }]}>
                              <Input prefix={<span className="lang-tag">UZ</span>} placeholder="6.7&quot; AMOLED" />
                            </Form.Item>
                            <Form.Item name={[name, 'name_ru']} noStyle>
                              <Input prefix={<span className="lang-tag ru">RU</span>} placeholder="Экран" />
                            </Form.Item>
                            <Form.Item name={[name, 'value_ru']} noStyle>
                              <Input prefix={<span className="lang-tag ru">RU</span>} placeholder="Значение" />
                            </Form.Item>
                          </div>
                        </Col>
                        <Col flex="none">
                          <Space size={4}>
                            <Button size="small" disabled={i === 0} onClick={() => move(i, i - 1)}>↑</Button>
                            <Button size="small" disabled={i === fields.length - 1} onClick={() => move(i, i + 1)}>↓</Button>
                            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => remove(name)} />
                          </Space>
                        </Col>
                      </Row>
                    ))}
                    <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add({ name: '', value: '', name_ru: '', value_ru: '' })}>
                      Xususiyat qo'shish
                    </Button>
                  </>
                )}
              </Form.List>
            </Card>

            <Card title="Rasmlar" style={{ marginBottom: 16 }}>
              {isNew ? (
                <Alert type="info" showIcon title="Rasmlarni mahsulot saqlangandan keyin yuklash mumkin." />
              ) : (
                <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Typography.Text strong>Asosiy rasm</Typography.Text>
                    <div style={{ marginTop: 8 }}>
                      <ImageUpload rule="product" path={`/admin/products/${id}/upload/`} value={product.image}
                                   onChange={p => setProduct({ ...product, image: p.image })} />
                    </div>
                  </div>
                  <div>
                    <Typography.Text strong>Qo'shimcha rasmlar</Typography.Text>
                    <div style={{ marginTop: 8 }}><Gallery product={product} onChange={setProduct} /></div>
                  </div>
                </Space>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="Narx va ombor" style={{ marginBottom: 16 }}>
              <Form.Item name="price" label="Narxi" rules={[{ required: true, message: 'Narxni kiriting' }]}>
                <InputNumber min={0} style={{ width: '100%' }} suffix="so'm" {...moneyInput} />
              </Form.Item>
              <Form.Item name="old_price" label="Eski narxi (chegirma uchun)"
                         extra={discount ? `Chegirma: -${discount}%` : 'Bo\'sh bo\'lsa chegirma yo\'q'}>
                <InputNumber min={0} style={{ width: '100%' }} suffix="so'm" {...moneyInput} />
              </Form.Item>
              {price > 0 && (
                <Alert type="warning" style={{ marginBottom: 16 }}
                       title={`Muddatli to'lov: ${formatPrice(price / 12)} × 12 oy`} />
              )}
              <Form.Item name="stock" label="Ombordagi soni" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} suffix="dona" />
              </Form.Item>
              {!isNew && <Typography.Text type="secondary">Sotilgan: {product.sold} dona</Typography.Text>}
            </Card>

            <Card title="Ko'rinish">
              <Form.Item name="is_active" label="Saytda ko'rinadi" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="is_hit" label="Xit savdo" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="is_new" label="Yangi" valuePropName="checked" style={{ marginBottom: 0 }}>
                <Switch />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16, whiteSpace: 'pre-line' }} />}
        <Space>
          {canEdit && <Button type="primary" htmlType="submit" loading={saving} size="large">Saqlash</Button>}
          <Button size="large" onClick={() => navigate('/products')}>Orqaga</Button>
        </Space>
      </Form>
    </>
  )
}
