import { useState } from 'react'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { errorText } from '../api'
import { useAuth } from '../auth'

export default function Login() {
  const { login } = useAuth()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async ({ username, password }) => {
    setError(''); setLoading(true)
    try {
      await login(username, password)
    } catch (err) {
      setError(err.status === 401 ? 'Login yoki parol noto\'g\'ri' : errorText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-wrap">
      <Card className="login-card">
        <Typography.Title level={3} style={{ textAlign: 'center', marginTop: 0 }}>
          <span style={{ color: '#ff6a00' }}>T</span>echShop <small style={{ fontWeight: 400, color: '#999' }}>admin</small>
        </Typography.Title>
        <Form layout="vertical" onFinish={submit} requiredMark={false}>
          <Form.Item name="username" label="Login" rules={[{ required: true, message: 'Loginni kiriting' }]}>
            <Input prefix={<UserOutlined />} size="large" autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="Parol" rules={[{ required: true, message: 'Parolni kiriting' }]}>
            <Input.Password prefix={<LockOutlined />} size="large" autoComplete="current-password" />
          </Form.Item>
          {error && <Alert type="error" title={error} style={{ marginBottom: 16 }} showIcon />}
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>Kirish</Button>
        </Form>
      </Card>
    </div>
  )
}
