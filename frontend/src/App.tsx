import React, { useState } from 'react';
import { Switch } from 'antd';
import Menu from 'antd/es/menu';
import Layout from 'antd/es/layout';
import theme from 'antd/es/theme';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import { 
  UserOutlined, 
  LockOutlined, 
  TeamOutlined, 
  ShopOutlined,
  SkinOutlined,
  CrownOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { Provider, useSelector } from 'react-redux';
import { ConfigProvider } from 'antd';
import esES from 'antd/lib/locale/es_ES';
import { RootState, store } from './store';
import Login from './components/Login';
import Register from './components/Register';
import CreateAccount from './components/CreateAccount';
import Dashboard from './components/Dashboard';
import TenantsList from './components/TenantsList';
import LicensesList from './components/LicensesList';
import UsersList from './components/UsersList';
import SuperAdminDashboard from './components/SuperAdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import HistoryPage from './components/HistoryPage';
import './App';
import { getDashboardPath, isSuperUser, isTenantUser } from './utils/authRouting';

const { Header, Content, Footer, Sider } = Layout;

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [darkMode, setDarkMode] = useState(false);
  const { user } = useSelector((state: RootState) => state.auth);
  const superUser = isSuperUser(user);
  const tenantUser = isTenantUser(user);
  
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const menuItems = [
    {
      key: 'dashboard',
      icon: <UserOutlined />,
      label: <Link to={getDashboardPath(user)}>Dashboard</Link>,
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: <Link to="/historia">Historia</Link>,
    },
    {
      key: 'tenants',
      icon: <TeamOutlined />,
      label: <Link to="/tenants">Empresas</Link>,
      hidden: !tenantUser,
    },
    {
      key: 'licenses',
      icon: <LockOutlined />,
      label: <Link to="/licenses">Licencias</Link>,
      hidden: !tenantUser,
    },
    {
      key: 'users',
      icon: <ShopOutlined />,
      label: <Link to="/users">Usuarios</Link>,
      hidden: !tenantUser,
    },
    {
      key: 'super-admin',
      icon: <CrownOutlined />,
      label: <Link to="/super-admin">Admin Global</Link>,
      hidden: !superUser,
    },
  ].filter((item) => !item.hidden);

  return (
    <Layout hasSider style={{ minHeight: '100vh' }}>
      <Sider
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
        theme={darkMode ? 'dark' : 'light'}
      >
        <div 
          className="logo" 
          style={{ 
            padding: '16px', 
            textAlign: 'center', 
            color: '#fff', 
            fontSize: '18px',
            backgroundColor: '#1B365D'
          }}
        >
          <h4 style={{ color: 'white', margin: 0 }}>Guayabera ERP v2.0</h4>
        </div>
        <Menu
          items={menuItems}
          theme={darkMode ? 'dark' : 'light'}
          mode="inline"
          defaultSelectedKeys={['dashboard']}
        />
      </Sider>
      <Layout style={{ marginLeft: 200 }}>
        <Header 
          style={{ 
            padding: '0 24px', 
            background: colorBgContainer,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <SkinOutlined style={{ marginRight: 8 }} />
            <span>Tema:</span>
            <div style={{ marginLeft: 8 }}>
              <Switch 
                checked={darkMode} 
                onChange={setDarkMode} 
                checkedChildren="Oscuro"
                unCheckedChildren="Claro"
              />
            </div>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div style={{ padding: 24, textAlign: 'center', background: colorBgContainer, minHeight: 360 }}>
            {children}
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          Guayabera ERP Suite v2.0 ©2026 - {" "}
          <span style={{ color: '#1B365D' }}>Azul Profundo</span>, 
          {" "} <span style={{ color: '#2E8B57' }}>Verde Empresarial</span>, 
          {" "} <span style={{ color: '#FF8C42' }}>Naranja Destaque</span>
        </Footer>
      </Layout>
    </Layout>
  );
};

const HomeRoute: React.FC = () => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  if (isAuthenticated) {
    return <Navigate to={getDashboardPath(user)} replace />;
  }

  return <HistoryPage />;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/historia" element={
            <MainLayout>
              <HistoryPage />
            </MainLayout>
          } />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/crear-cuenta/:token" element={<CreateAccount />} />
          <Route path="/dashboard" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <Dashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/tenants" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <TenantsList />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/licenses" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <LicensesList />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/users" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <UsersList />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/super-admin" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['superuser', 'superadmin']}>
                <SuperAdminDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ConfigProvider locale={esES}>
        <AppRoutes />
      </ConfigProvider>
    </Provider>
  );
};

export default App;
