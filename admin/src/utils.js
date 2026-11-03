export const formatPrice = n =>
  `${String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} so'm`

export const formatNumber = n => String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

export const ORDER_STATUS = {
  new: { label: 'Yangi', color: 'blue' },
  confirmed: { label: 'Tasdiqlangan', color: 'cyan' },
  shipped: { label: 'Yuborilgan', color: 'orange' },
  delivered: { label: 'Yetkazilgan', color: 'green' },
  cancelled: { label: 'Bekor qilingan', color: 'red' },
}

export const PAYMENT = {
  cash: 'Naqd pul',
  card: 'Karta',
  click: 'Click',
  payme: 'Payme',
  paynet: 'Paynet',
  uzum: 'Uzum Bank',
  installment: 'Muddatli to\'lov',
}

export const DELIVERY = {
  courier: 'Kuryer',
  pickup: 'Olib ketish',
}

export const options = map =>
  Object.entries(map).map(([value, v]) => ({ value, label: typeof v === 'string' ? v : v.label }))

// "1 500 000" ko'rinishida yozish uchun InputNumber formatter
export const moneyInput = {
  formatter: v => (v === undefined || v === null || v === '' ? '' : formatNumber(v)),
  parser: v => (v ? v.replace(/\D/g, '') : ''),
}

// Sahifa almashganda jadval boshiga qaytish (pagination pastda turadi)
export function scrollToTable() {
  const table = () => document.querySelector('.ant-table-wrapper')
  requestAnimationFrame(() => table()?.scrollIntoView({ block: 'start' }))
  // Yangi sahifa yuklangach balandlik o'zgaradi — yuklanish tugagach yana bir marta tekislaymiz
  const started = Date.now()
  const timer = setInterval(() => {
    const loading = document.querySelector('.ant-table-wrapper .ant-spin-spinning')
    if (!loading || Date.now() - started > 4000) {
      clearInterval(timer)
      setTimeout(() => table()?.scrollIntoView({ block: 'start' }), 50)
    }
  }, 100)
}
