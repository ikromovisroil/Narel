import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { App as AntApp, ConfigProvider } from 'antd'
import uzUZ from 'antd/locale/uz_UZ'
import dayjs from 'dayjs'
import 'dayjs/locale/uz-latn'
import App from './App.jsx'
import { AuthProvider } from './auth.jsx'
import './index.css'

dayjs.locale('uz-latn')

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ConfigProvider
      locale={uzUZ}
      theme={{ token: { colorPrimary: '#1f5eff', borderRadius: 8, fontFamily: 'Inter, system-ui, sans-serif' } }}
    >
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </StrictMode>,
)
