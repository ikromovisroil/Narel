import {
  AppstoreOutlined, CommentOutlined, DashboardOutlined, IdcardOutlined, PictureOutlined, SettingOutlined, ShoppingCartOutlined,
  ShoppingOutlined, TagsOutlined, TeamOutlined,
} from '@ant-design/icons'

// Menyu bandlari va ularning bo'limlari (backenddagi staff.models.SECTIONS bilan bir xil)
export const MENU = [
  { key: '/', section: 'dashboard', icon: <DashboardOutlined />, label: 'Bosh sahifa' },
  { key: '/orders', section: 'orders', icon: <ShoppingCartOutlined />, label: 'Buyurtmalar' },
  { key: '/products', section: 'products', icon: <ShoppingOutlined />, label: 'Mahsulotlar' },
  { key: '/categories', section: 'categories', icon: <AppstoreOutlined />, label: 'Kategoriyalar' },
  { key: '/brands', section: 'brands', icon: <TagsOutlined />, label: 'Brendlar' },
  { key: '/banners', section: 'banners', icon: <PictureOutlined />, label: 'Bannerlar' },
  { key: '/customers', section: 'customers', icon: <TeamOutlined />, label: 'Mijozlar' },
  { key: '/comments', section: 'comments', icon: <CommentOutlined />, label: 'Izohlar' },
  { key: '/staff', section: 'staff', icon: <IdcardOutlined />, label: 'Xodimlar' },
  { key: '/settings', section: 'settings', icon: <SettingOutlined />, label: 'Sozlamalar' },
]
