import React, { useState } from 'react';
import { Layout, Typography, ConfigProvider, Menu } from 'antd';
import SearchPage from './components/SearchPage';
import AdminPage from './components/AdminPage';
import LoginPage from './components/LoginPage';
import FAQPage from './components/FAQPage';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { SearchOutlined, QuestionCircleOutlined, UserOutlined } from '@ant-design/icons';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

// 导航菜单组件
const NavigationMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/') return 'search';
    if (path === '/faq') return 'faq';
    if (path.startsWith('/admin')) return 'admin';
    return 'search';
  };

  return (
    <Menu 
      mode="horizontal" 
      selectedKeys={[getSelectedKey()]} 
      style={{ 
        border: 'none', 
        flex: 1,
        justifyContent: 'flex-end',
        marginRight: '20px'
      }}
    >
      <Menu.Item 
        key="search" 
        icon={<SearchOutlined />} 
        onClick={() => navigate('/')}
      >
        查询
      </Menu.Item>
      <Menu.Item 
        key="faq" 
        icon={<QuestionCircleOutlined />} 
        onClick={() => navigate('/faq')}
      >
        常见问题
      </Menu.Item>
      <Menu.Item 
        key="admin" 
        icon={<UserOutlined />} 
        onClick={() => navigate('/admin/login')}
      >
        管理后台
      </Menu.Item>
    </Menu>
  );
};

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <Router>
        <Layout className="layout">
          <Header style={{ 
            background: '#fff', 
            padding: '0 50px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <Title level={2} style={{ margin: '16px 0', color: '#000' }}>自助查询工具</Title>
            <NavigationMenu />
          </Header>
          <Content style={{ 
            padding: '0 50px', 
            minHeight: 'calc(100vh - 64px)',
            background: '#f0f2f5'
          }}>
            <div className="site-layout-content">
              <Routes>
                <Route path="/" element={<SearchPage />} />
                <Route path="/faq" element={<FAQPage />} />
                <Route path="/admin/login" element={<LoginPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="/admin/*" element={<Navigate to="/admin/login" replace />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </Router>
    </ConfigProvider>
  );
};

export default App; 