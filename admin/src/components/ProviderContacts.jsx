import { Typography } from 'antd'
import { LinkOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons'

const icon = url => (url.startsWith('tel:') ? <PhoneOutlined /> : url.startsWith('mailto:') ? <MailOutlined /> : <LinkOutlined />)

// To'lov tizimi bilan ulanish uchun kimga murojaat qilish: havolalar, telefonlar, hujjatlar
export default function ProviderContacts({ contacts, compact = false }) {
  if (!contacts || (!contacts.links.length && !contacts.note)) return null
  return (
    <div className={`contact-box ${compact ? 'compact' : ''}`}>
      {!compact && <b>Kimga murojaat qilish</b>}
      <ul>
        {contacts.links.map(c => (
          <li key={c.url}>
            <span className="contact-label">{c.label}:</span>{' '}
            <a href={c.url} target={c.url.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
              {icon(c.url)} {c.value}
            </a>
          </li>
        ))}
      </ul>
      {contacts.documents?.length > 0 && (
        <Typography.Paragraph style={{ margin: '6px 0 0', fontSize: 13 }}>
          <b>Kerakli hujjatlar:</b> {contacts.documents.join('; ')}.
        </Typography.Paragraph>
      )}
      {contacts.note && (
        <Typography.Paragraph type="secondary" style={{ margin: '6px 0 0', fontSize: 13 }}>{contacts.note}</Typography.Paragraph>
      )}
    </div>
  )
}
