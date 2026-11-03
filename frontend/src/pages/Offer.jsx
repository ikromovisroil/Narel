import { useEffect, useState } from 'react'
import { api } from '../api'
import { dateLocale, t } from '../i18n'
import { useStore } from '../store'

// Matnni bo'limlarga ajratadi: "# " bilan boshlangan qator — sarlavha, qolganlari — xatboshilar
function parse(text) {
  const intro = []
  const sections = []
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    if (line.startsWith('# ')) sections.push({ title: line.slice(2), lines: [] })
    else (sections.at(-1)?.lines || intro).push(line)
  }
  return { intro, sections }
}

// Ommaviy oferta — matni admin Sozlamalarida kiritiladi
export default function Offer() {
  const { lang } = useStore()
  const [data, setData] = useState(null)

  useEffect(() => { api('/offer/', { auth: false }).then(setData).catch(() => setData({ text: '' })) }, [lang])

  if (!data) return <div className="muted">{t('Yuklanmoqda...')}</div>
  const { intro, sections } = parse(data.text || '')

  return (
    <div className="offer-page">
      {sections.length > 1 && (
        <nav className="pcard offer-toc">
          <b>{t('Mundarija')}</b>
          {sections.map((s, i) => <a key={i} href={`#offer-${i + 1}`}>{s.title}</a>)}
        </nav>
      )}
      <article className="pcard offer">
        <h1 className="page-title">{t('Ommaviy oferta')}</h1>
        {!data.text ? <p className="muted">{t('Oferta matni hali kiritilmagan.')}</p> : (
          <>
            {intro.map((p, i) => <p key={i} className="offer-intro">{p}</p>)}
            {sections.map((s, i) => (
              <section key={i} id={`offer-${i + 1}`}>
                <h2>{s.title}</h2>
                {s.lines.map((p, j) => <p key={j}>{p}</p>)}
              </section>
            ))}
            {data.updated_at && (
              <p className="muted small">{t('Yangilangan: {date}', { date: new Date(data.updated_at).toLocaleDateString(dateLocale()) })}</p>
            )}
          </>
        )}
      </article>
    </div>
  )
}
