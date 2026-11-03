import { useSearchParams } from 'react-router-dom'

// Maydon: sarlavha, input va xato matni
export function Field({ label, required, error, children }) {
  return (
    <label>
      <span>{label}{required && <> <span className="req">*</span></>}</span>
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

// Kirgandan keyin qaytiladigan sahifa (faqat sayt ichidagi manzil)
export function useNext() {
  const [params] = useSearchParams()
  const next = params.get('next') || '/'
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
}
