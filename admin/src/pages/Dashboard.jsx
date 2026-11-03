import { useEffect, useState } from 'react'
import { Card, Col, Empty, Row, Segmented, Spin, Statistic, Table, Tag, Typography } from 'antd'
import {
  DollarOutlined, ShoppingCartOutlined, TeamOutlined, WarningOutlined,
} from '@ant-design/icons'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import dayjs from 'dayjs'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { formatNumber, formatPrice, ORDER_STATUS } from '../utils'

// Oddiy ro'yxat: chapda matn, o'ngda qiymat
function SimpleList({ items, render }) {
  return (
    <div>
      {items.map((item, i) => {
        const [left, right] = render(item, i)
        return (
          <div key={item.id} style={{
            display: 'flex', justifyContent: 'space-between', gap: 12, padding: '8px 0',
            borderBottom: i < items.length - 1 ? '1px solid #f0f0f0' : 'none',
          }}>
            <span>{left}</span><span style={{ whiteSpace: 'nowrap' }}>{right}</span>
          </div>
        )
      })}
    </div>
  )
}

const short = n => (n >= 1e9 ? `${(n / 1e9).toFixed(1)} mlrd` : n >= 1e6 ? `${(n / 1e6).toFixed(1)} mln` : formatNumber(n))

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [metric, setMetric] = useState('revenue')
  const navigate = useNavigate()

  useEffect(() => { api('/admin/stats/').then(setStats) }, [])

  if (!stats) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

  const cards = [
    { title: 'Bugungi savdo', value: formatPrice(stats.today.revenue), sub: `${stats.today.orders} ta buyurtma`, icon: <DollarOutlined />, color: '#1f5eff' },
    { title: 'Shu oy', value: formatPrice(stats.month.revenue), sub: `${stats.month.orders} ta buyurtma`, icon: <ShoppingCartOutlined />, color: '#17a34a' },
    { title: 'Yangi buyurtmalar', value: stats.new_orders, sub: 'Ko\'rib chiqilishi kerak', icon: <ShoppingCartOutlined />, color: '#ff6a00', link: '/orders?status=new' },
    { title: 'Mijozlar', value: stats.customers, sub: `${stats.products} ta mahsulot`, icon: <TeamOutlined />, color: '#7c3aed', link: '/customers' },
  ]

  const chart = stats.chart.map(d => ({ ...d, label: dayjs(d.date).format('DD.MM') }))

  return (
    <>
      <Typography.Title level={3} style={{ marginTop: 0 }}>Bosh sahifa</Typography.Title>

      <Row gutter={[16, 16]}>
        {cards.map(c => (
          <Col xs={24} sm={12} xl={6} key={c.title}>
            <Card hoverable={Boolean(c.link)} onClick={() => c.link && navigate(c.link)}>
              <Statistic
                title={c.title} value={c.value}
                prefix={<span style={{ color: c.color, marginRight: 4 }}>{c.icon}</span>}
              />
              <Typography.Text type="secondary">{c.sub}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xl={16}>
          <Card
            title="Oxirgi 30 kun"
            extra={<Segmented value={metric} onChange={setMetric}
                              options={[{ value: 'revenue', label: 'Savdo' }, { value: 'orders', label: 'Buyurtmalar' }]} />}
          >
            <ResponsiveContainer width="100%" height={300}>
              {metric === 'revenue' ? (
                <AreaChart data={chart} margin={{ left: 8, right: 8 }}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1f5eff" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#1f5eff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
                  <YAxis tickFormatter={short} tick={{ fontSize: 12 }} width={70} />
                  <Tooltip formatter={v => [formatPrice(v), 'Savdo']} />
                  <Area type="monotone" dataKey="revenue" stroke="#1f5eff" strokeWidth={2} fill="url(#rev)" />
                </AreaChart>
              ) : (
                <BarChart data={chart} margin={{ left: 8, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} width={40} />
                  <Tooltip formatter={v => [v, 'Buyurtmalar']} />
                  <Bar dataKey="orders" fill="#ff6a00" radius={[4, 4, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} xl={8}>
          <Card title="Eng ko'p sotilganlar" style={{ marginBottom: 16 }}>
            {stats.top_products.length ? (
              <SimpleList items={stats.top_products} render={(p, i) => [
                <Link key="l" to={`/products/${p.id}`}>{i + 1}. {p.name}</Link>, <b key="r">{p.qty} dona</b>,
              ]} />
            ) : <Empty description="Hali sotuv yo'q" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
          </Card>
          <Card title={<><WarningOutlined style={{ color: '#e5383b' }} /> Kam qolgan mahsulotlar</>}
                extra={<Link to="/products?low_stock=true">Barchasi</Link>}>
            {stats.low_stock.length ? (
              <SimpleList items={stats.low_stock} render={p => [
                <Link key="l" to={`/products/${p.id}`}>{p.name}</Link>,
                <Tag key="r" color={p.stock === 0 ? 'red' : 'orange'}>{p.stock} dona</Tag>,
              ]} />
            ) : <Empty description="Hammasi yetarli" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
          </Card>
        </Col>
      </Row>

      <Card title="So'nggi buyurtmalar" style={{ marginTop: 16 }} extra={<Link to="/orders">Barchasi</Link>}>
        <Table
          rowKey="id" dataSource={stats.recent_orders} pagination={false} size="middle"
          scroll={{ x: 600 }}
          onRow={o => ({ onClick: () => navigate(`/orders?open=${o.id}`), style: { cursor: 'pointer' } })}
          columns={[
            { title: '№', dataIndex: 'id', render: id => `#${id}` },
            { title: 'Mijoz', dataIndex: 'full_name' },
            { title: 'Telefon', dataIndex: 'phone' },
            { title: 'Summa', dataIndex: 'total', render: formatPrice },
            { title: 'Holati', dataIndex: 'status', render: s => <Tag color={ORDER_STATUS[s].color}>{ORDER_STATUS[s].label}</Tag> },
            { title: 'Sana', dataIndex: 'created_at', render: d => dayjs(d).format('DD.MM.YYYY HH:mm') },
          ]}
        />
      </Card>
    </>
  )
}
