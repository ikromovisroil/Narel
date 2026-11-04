import { useEffect, useState } from 'react'
import { Avatar, Badge, Button, Dropdown, Grid, Layout, Menu, Tooltip } from 'antd'
import {
  LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, SendOutlined, UserOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { api } from './api'
import { useAuth } from './auth'
import { MENU } from './menu'
import { LogoMark } from './LogoMark'

const { Header, Sider, Content } = Layout


export default function AdminLayout() {
  const { user, logout, can } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const screens = Grid.useBreakpoint()
  const mobile = !screens.lg
  const [collapsed, setCollapsed] = useState(mobile)
  const [newOrders, setNewOrders] = useState(0)

  // Yangi buyurtmalar sonini har daqiqada yangilab turamiz
  useEffect(() => {
    if (!can('orders')) return undefined
    const load = () => api('/admin/orders/', { params: { status: 'new', page_size: 1 } })
      .then(r => setNewOrders(r.count)).catch(() => {})
    load()
    const t = setInterval(load, 60000)
    window.addEventListener('orders-changed', load)
    return () => {
      clearInterval(t)
      window.removeEventListener('orders-changed', load)
    }
  }, [pathname]) // eslint-disable-line react-hooks/exhaustive-deps

  // Menyuda faqat ruxsati bor bo'limlar ko'rinadi
  const items = MENU.filter(m => can(m.section)).map(({ section: _section, ...m }) => (
    m.key === '/orders'
      ? { ...m, label: <span>Buyurtmalar <Badge count={newOrders} size="small" offset={[6, -2]} /></span> }
      : m
  ))
  const selected = items.map(i => i.key).filter(k => k !== '/' && pathname.startsWith(k))[0] || '/'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible collapsed={collapsed} onCollapse={setCollapsed} trigger={null}
        breakpoint="lg" collapsedWidth={mobile ? 0 : 80} width={232}
        style={mobile ? { position: 'fixed', height: '100vh', zIndex: 100 } : { position: 'sticky', top: 0, height: '100vh' }}
      >
        <div className="logo">
          <LogoMark size={30} dark />
          {!collapsed && <><span>Narel</span><small>admin</small></>}
        </div>
        <Menu
          theme="dark" mode="inline" selectedKeys={[selected]} items={items}
          onClick={({ key }) => { navigate(key); if (mobile) setCollapsed(true) }}
        />
        <Tooltip title={collapsed ? 'Dasturchi: Ikromov.I' : ''} placement="right">
          <a className="dev-credit" href="https://t.me/Isroil_0309" target="_blank" rel="noopener noreferrer">
            {collapsed ? <SendOutlined /> : <>Dasturchi: <b>Ikromov.I</b></>}
          </a>
        </Tooltip>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 16px', display: 'flex', alignItems: 'center', gap: 12, position: 'sticky', top: 0, zIndex: 10, boxShadow: '0 1px 0 #eee' }}>
          <Button type="text" onClick={() => setCollapsed(c => !c)}
                  icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} />
          <div style={{ flex: 1 }} />
          <Button href="http://localhost:5173" target="_blank" type="link">Saytni ochish ↗</Button>
          <Dropdown menu={{ items: [{ key: 'logout', icon: <LogoutOutlined />, label: 'Chiqish', onClick: logout }] }}>
            <span style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} style={{ background: '#1f5eff' }} />
              {!mobile && (user.first_name || user.username)}
            </span>
          </Dropdown>
        </Header>
        <Content style={{ padding: mobile ? 12 : 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
