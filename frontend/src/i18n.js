// Sayt tillari: uz (asosiy) va ru (lug'atdan).
// Kalit sifatida o'zbekcha matnning o'zi ishlatiladi: t("Savatga").
import ru from './locales/ru'

export const LANGS = [
  { code: 'uz', label: "O'zb" },
  { code: 'ru', label: 'Рус' },
]

let current = (() => {
  try {
    const saved = localStorage.getItem('lang')
    return LANGS.some(l => l.code === saved) ? saved : 'uz'
  } catch {
    return 'uz'
  }
})()

export const getLang = () => current
export function setLang(code) {
  current = code
  try { localStorage.setItem('lang', code) } catch { /* brauzer xotirasi yopiq */ }
  document.documentElement.lang = code
}
setLang(current)

// {name} kabi o'zgaruvchilar tarjimadan keyin qo'yiladi
export function t(text, vars) {
  let s = current === 'ru' ? (ru[text] ?? text) : text
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m))
  return s
}

export const dateLocale = () => (current === 'ru' ? 'ru-RU' : 'uz-UZ')
