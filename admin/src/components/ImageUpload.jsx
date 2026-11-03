import { useState } from 'react'
import { App, Button, Image, Space, Typography, Upload } from 'antd'
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons'
import { api, errorText, upload } from '../api'
import { acceptFor, checkImage, ruleHint, useImageRule } from '../imageRules'

/**
 * Bitta rasmni yuklash/o'chirish. `path` — masalan "/admin/brands/3/upload/".
 * `rule` — rasm talablari kaliti: product | category | brand | banner.
 * onChange serverdan qaytgan yangilangan obyektni oladi.
 */
export default function ImageUpload({ path, rule: ruleKey, value, onChange, label = 'Rasm yuklash' }) {
  const { message } = App.useApp()
  const rule = useImageRule(ruleKey)
  const [busy, setBusy] = useState(false)

  const ratio = rule ? rule.ratio[0] / rule.ratio[1] : 1
  const previewH = 96
  const previewW = Math.min(Math.round(previewH * ratio), 320)

  const send = async file => {
    const problem = await checkImage(file, rule)
    if (problem) {
      message.error({ content: problem, duration: 6 })
      return Upload.LIST_IGNORE
    }
    setBusy(true)
    try {
      onChange(await upload(path, file))
      message.success('Rasm yuklandi')
    } catch (err) {
      message.error({ content: errorText(err), duration: 6 })
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
    <div>
      <Space align="center" wrap>
        {value && (
          <Image src={value} width={previewW} height={previewH}
                 style={{ objectFit: 'contain', background: '#f4f6fb', borderRadius: 8 }} />
        )}
        <Upload accept={acceptFor(rule)} showUploadList={false} beforeUpload={send}>
          <Button icon={<UploadOutlined />} loading={busy}>{value ? 'Almashtirish' : label}</Button>
        </Upload>
        {value && <Button danger icon={<DeleteOutlined />} onClick={remove} disabled={busy} />}
      </Space>
      {rule && (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, margin: '6px 0 0' }}>
          {ruleHint(rule)}<br />{rule.hint}
        </Typography.Paragraph>
      )}
    </div>
  )
}
