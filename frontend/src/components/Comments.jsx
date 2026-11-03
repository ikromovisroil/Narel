import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api, errorText } from '../api'
import { t } from '../i18n'
import { useStore } from '../store'
import ConfirmButton from './ConfirmButton'

function Stars({ value, onChange, size = 18 }) {
  return (
    <span className="stars" style={{ fontSize: size }}>
      {[1, 2, 3, 4, 5].map(n => (
        onChange ? (
          <button key={n} type="button" className={n <= (value || 0) ? 'on' : ''} onClick={() => onChange(value === n ? null : n)}
                  aria-label={`${n}`}>★</button>
        ) : <span key={n} className={n <= (value || 0) ? 'on' : ''}>★</span>
      ))}
    </span>
  )
}

function CommentForm({ onSubmit, placeholder, withRating, autoFocus, onCancel, submitLabel }) {
  const [text, setText] = useState('')
  const [rating, setRating] = useState(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const submit = async e => {
    e.preventDefault()
    setSending(true); setError('')
    try {
      await onSubmit({ text, rating })
      setText(''); setRating(null)
    } catch (err) {
      setError(err.status === 429 ? t("Juda ko'p izoh yubordingiz. Birozdan keyin urinib ko'ring.") : errorText(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <form className="comment-form" onSubmit={submit}>
      {withRating && (
        <div className="rate-row"><span className="muted small">{t('Bahoingiz (ixtiyoriy)')}:</span><Stars value={rating} onChange={setRating} size={22} /></div>
      )}
      <textarea rows={withRating ? 3 : 2} maxLength={1000} required value={text} autoFocus={autoFocus}
                onChange={e => setText(e.target.value)} placeholder={placeholder} />
      {error && <div className="error">{error}</div>}
      <div className="comment-form-actions">
        <span className="muted small">{text.length}/1000</span>
        {onCancel && <button type="button" className="link" onClick={onCancel}>{t('Bekor qilish')}</button>}
        <button className="btn btn-sm" disabled={sending || text.trim().length < 2}>
          {sending ? t('Yuborilmoqda...') : submitLabel}
        </button>
      </div>
    </form>
  )
}

function CommentItem({ c, onReply, onDelete, isReply }) {
  const initial = (c.author || '?')[0].toUpperCase()
  return (
    <div className={`comment ${isReply ? 'reply' : ''}`}>
      <div className={`comment-avatar ${c.is_staff ? 'staff' : ''}`}>{initial}</div>
      <div className="comment-body">
        <div className="comment-head">
          <b>{c.author}</b>
          {c.is_staff && <span className="tag tag-staff">{t("Do'kon")}</span>}
          {c.rating && <Stars value={c.rating} size={14} />}
          <span className="muted small">{new Date(c.created_at).toLocaleDateString('ru-RU')}</span>
        </div>
        <p className="comment-text">{c.text}</p>
        <div className="comment-actions">
          {onReply && <button className="link small" onClick={onReply}>{t('Javob berish')}</button>}
          {c.is_mine && (
            <ConfirmButton className="link small danger" title={t("Izohni o'chirasizmi?")} okLabel={t("O'chirish")}
                           onConfirm={() => onDelete(c)}>
              {t("O'chirish")}
            </ConfirmButton>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Comments({ slug, onSummary }) {
  const { user } = useStore()
  const location = useLocation()
  const [items, setItems] = useState([])
  const [next, setNext] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [replyTo, setReplyTo] = useState(null)

  const load = async (page = 1) => {
    setLoading(true)
    try {
      const r = await api(`/products/${slug}/comments/?page=${page}`, { auth: Boolean(user) })
      setItems(list => (page === 1 ? r.results : [...list, ...r.results]))
      setNext(r.next ? page + 1 : null)
      setSummary(r.summary)
      onSummary?.(r.summary)
    } finally {
      setLoading(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(1) }, [slug, user])

  const send = async body => {
    await api(`/products/${slug}/comments/`, { method: 'POST', body })
    setReplyTo(null)
    await load(1)
  }

  const remove = async c => {
    await api(`/comments/${c.id}/`, { method: 'DELETE' })
    await load(1)
  }

  return (
    <div className="comments">
      {summary?.rating && (
        <div className="rating-summary">
          <span className="rating-big">{summary.rating}</span>
          <Stars value={Math.round(summary.rating)} size={20} />
          <span className="muted small">{t('{n} ta baho', { n: summary.ratings_count })}</span>
        </div>
      )}

      {user ? (
        <CommentForm withRating onSubmit={send} submitLabel={t('Yuborish')}
                     placeholder={t("Mahsulot haqida fikringizni yozing yoki savol bering...")} />
      ) : (
        <div className="comment-login">
          {t("Izoh qoldirish uchun tizimga kiring")}{' '}
          <Link className="btn btn-sm" to={`/login?next=${encodeURIComponent(location.pathname)}`}>{t('Kirish')}</Link>
        </div>
      )}

      {!loading && !items.length && <p className="muted">{t("Hali izoh yo'q. Birinchi bo'lib fikr bildiring!")}</p>}

      {items.map(c => (
        <div key={c.id} className="thread">
          <CommentItem c={c} onDelete={remove} onReply={user ? () => setReplyTo(replyTo === c.id ? null : c.id) : null} />
          <div className="thread-replies">
            {c.replies.map(r => (
              <CommentItem key={r.id} c={r} isReply onDelete={remove}
                           onReply={user ? () => setReplyTo(c.id) : null} />
            ))}
            {replyTo === c.id && (
              <CommentForm autoFocus onSubmit={body => send({ ...body, parent: c.id })} onCancel={() => setReplyTo(null)}
                           submitLabel={t('Javob berish')} placeholder={t('{name} ga javob...', { name: c.author })} />
            )}
          </div>
        </div>
      ))}

      {next && (
        <button className="btn btn-outline btn-sm" disabled={loading} onClick={() => load(next)}>
          {loading ? t('Yuklanmoqda...') : t("Ko'proq ko'rsatish")}
        </button>
      )}
    </div>
  )
}
