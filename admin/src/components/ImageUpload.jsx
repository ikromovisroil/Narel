import { useState } from 'react'
import { App, Button, Image, Space, Upload } from 'antd'
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons'
import { api, errorText, upload } from '../api'

/**
 * Bitta rasmni yuklash/o'chirish. `path` — masalan "/admin/brands/3/upload/".
 * onChange serverdan qaytgan yangilangan obyektni oladi.
 */
export default function ImageUpload({ path, value, onChange, label = 'Rasm yuklash' }) {
  const { message } = App.useApp()
  const [busy, setBusy] = useState(false)

  const send = async file => {
    setBusy(true)
    try {
      onChange(await upload(path, file))
      message.success('Rasm yuklandi')
    } catch (err) {
      message.error(errorText(err))
    } finally {
      setBusy(false)
    }
    return false
  }

  const remove = async () => {
    setBusy(true)
    try {
      onChange(await api(path, { method: 'DELETE' }))
    } catch (err) {
      message.error(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Space align="center" wrap>
      {value && <Image src={value} width={96} height={96} style={{ objectFit: 'contain', background: '#f4f6fb', borderRadius: 8 }} />}
      <Upload accept="image/*" showUploadList={false} beforeUpload={send}>
        <Button icon={<UploadOutlined />} loading={busy}>{value ? 'Almashtirish' : label}</Button>
      </Upload>
      {value && <Button danger icon={<DeleteOutlined />} onClick={remove} disabled={busy} />}
    </Space>
  )
}
