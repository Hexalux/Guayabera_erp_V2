import React, { useState } from 'react';
import { Switch, Button } from 'antd';
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
  HistoryOutlined,
  BankOutlined,
  WalletOutlined,
  DollarOutlined
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

import { TreasuryDashboard } from './pages/finance/TreasuryDashboard';
import { AccountsReceivable } from './pages/finance/AccountsReceivable';
import { AccountsPayable } from './pages/finance/AccountsPayable';
import { ExpensesDashboard } from './pages/finance/ExpensesDashboard';
import ChartOfAccounts from './pages/finance/ChartOfAccounts';
import JournalEntries from './pages/finance/JournalEntries';
import InventoryDashboard from './pages/inventory/InventoryDashboard';
import ProductsList from './pages/inventory/ProductsList';
import StockMovements from './pages/inventory/StockMovements';
import { PhysicalInventory } from './pages/inventory/PhysicalInventory';
import { TrazabilidadVisor } from './pages/inventory/TrazabilidadVisor';
import { HRDashboard } from './pages/hr/HRDashboard';
import { EmployeeDirectory } from './pages/hr/EmployeeDirectory';
import { TimeOff } from './pages/hr/TimeOff';
// Módulos Nómina
import { Payroll } from './pages/hr/Payroll';
import { PayrollConfig } from './pages/hr/PayrollConfig';
import { FiscalConfig } from './pages/hr/FiscalConfig';
import { Checador } from './pages/hr/Checador';
import { PointOfSale } from './pages/sales/PointOfSale';
import { SalesHistory } from './pages/sales/SalesHistory';
import { B2BDashboard } from './pages/sales_b2b/B2BDashboard';
import { AccountingDashboard } from './pages/finance/AccountingDashboard';
import { JournalAudit } from './pages/finance/JournalAudit';
import { AgingReports } from './pages/finance/AgingReports';
import { AccountingSettings } from './pages/finance/AccountingSettings';
import { BankTransactions } from './pages/finance/BankTransactions';
import { PurchaseOrders } from './pages/purchases/PurchaseOrders';
import { Proveedores } from './pages/purchases/Proveedores';
import ProductionDashboard from './pages/production/ProductionDashboard';
import ProductionOrders from './pages/production/ProductionOrders';
import { ConfiguracionInventario } from './pages/inventory/ConfiguracionInventario';
import { SalesDashboard } from './pages/sales/SalesDashboard';
import { SalesOrders } from './pages/sales/SalesOrders';
import { Clientes } from './pages/sales/Clientes';
import { SalesConfig } from './pages/sales/SalesConfig';
import { SalesReports } from './pages/sales/SalesReports';
import { ProyectosProduccion } from './pages/production/ProyectosProduccion';
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
      key: 'finance',
      icon: <WalletOutlined />,
      label: 'Contabilidad',
      hidden: !tenantUser,
      children: [
        {
          key: 'fin-clientes',
          label: 'Clientes',
          children: [
            { key: 'fin-cxc', label: <Link to="/finance/cxc">Cuentas por Cobrar (CxC)</Link> },
          ]
        },
        {
          key: 'fin-proveedores',
          label: 'Proveedores',
          children: [
            { key: 'fin-cxp', label: <Link to="/finance/cxp">Cuentas por Pagar (CxP)</Link> },
            { key: 'fin-gastos', label: <Link to="/finance/expenses">Control de Gastos</Link> }
          ]
        },
        {
          key: 'fin-contabilidad',
          label: 'Asientos',
          children: [
            { key: 'inv-products', label: <Link to="/inventory/products">Catálogo de Productos</Link> },
            { key: 'inv-movements', label: <Link to="/inventory/movements">Movimientos de Almacén</Link> },
            { key: 'inv-physical', label: <Link to="/inventory/physical">Auditoría Física</Link> },
            { key: 'inv-traceability', label: <Link to="/inventory/traceability">Trazabilidad</Link> },
          ]
        },
        {
          key: 'fin-tesoreria',
          label: 'Tesorería',
          children: [
            { key: 'fin-bancos', label: <Link to="/finance/treasury">Bancos y Flujo</Link> },
            { key: 'fin-bank-ops', label: <Link to="/finance/transactions">Operaciones Bancarias</Link> }
          ]
        },
        {
          key: 'fin-gastos-main',
          label: 'Control de Gastos',
          icon: <WalletOutlined />,
          children: [
            { key: 'fin-expenses-dashboard', label: <Link to="/finance/expenses">Comprobaciones</Link> }
          ]
        },
        {
          key: 'fin-reportes',
          label: 'Reportes',
          children: [
            { key: 'op-b2b', label: <Link to="/sales-b2b">Portal B2B</Link> }
          ]
        },
        {
          key: 'admin-config',
          label: 'Configuración',
          children: [
            { key: 'fin-cuentas', label: <Link to="/finance/cuentas">Plan de Cuentas</Link> },
            { key: 'fin-settings', label: <Link to="/finance/settings">Fechas de Bloqueo</Link> }
          ]
        }
      ]
    },
    {
      key: 'hr',
      icon: <TeamOutlined />,
      label: 'Recursos Humanos',
      hidden: !tenantUser,
      children: [
        { key: 'hr-dashboard', label: <Link to="/hr">Portal Empleado</Link> },
        { key: 'hr-directory', label: <Link to="/hr/directory">Directorio</Link> },
        { key: 'hr-timeoff', label: <Link to="/hr/timeoff">Vacaciones / Faltas</Link> },
        { key: 'hr-checador', label: <Link to="/hr/checador">Reloj Checador</Link> }
      ]
    },
    {
      key: 'payroll',
      icon: <DollarOutlined />,
      label: 'Nómina',
      hidden: !tenantUser,
      children: [
        { key: 'hr-payroll', label: <Link to="/hr/payroll">Recibos de Nómina</Link> },
        { key: 'payroll-config', label: <Link to="/hr/payroll-config">Catálogos SAT</Link> },
        { key: 'fiscal-config', label: <Link to="/hr/fiscal-config">Configuración Fiscal (ISR/UMA)</Link> }
      ]
    },
    {
      key: 'inventory',
      icon: <ShopOutlined />,
      label: 'Inventario',
      hidden: !tenantUser,
      children: [
        {
          key: 'inventory-dashboard',
          label: <Link to="/inventory/dashboard">Resumen</Link>,
        },
        {
          key: 'inventory-productos',
          label: <Link to="/inventory/productos">Productos Textiles</Link>,
        },
        {
          key: 'inventory-movimientos',
          label: <Link to="/inventory/movimientos">Terminal Movimientos</Link>,
        },
        {
          key: 'inventory-config',
          label: <Link to="/inventory/config">Configuración</Link>,
        },
        {
          key: 'inventory-trazabilidad',
          label: <Link to="/inventory/trazabilidad">Visor Trazabilidad 360°</Link>,
        }
      ]
    },
    {
      key: 'production',
      icon: <SkinOutlined />,
      label: 'Producción',
      hidden: !tenantUser,
      children: [
        {
          key: 'production-dashboard',
          label: <Link to="/production/dashboard">Fábrica / Resumen</Link>,
        },
        {
          key: 'production-proyectos',
          label: <Link to="/production/proyectos">Proyectos</Link>,
        },
        {
          key: 'production-orders',
          label: <Link to="/production/orders">Órdenes de Producción</Link>,
        }
      ]
    },
    {
      key: 'sales',
      icon: <ShopOutlined />,
      label: 'Ventas',
      hidden: !tenantUser,
      children: [
        {
          key: 'sales-pos',
          label: <Link to="/sales/pos">Punto de Venta (POS)</Link>,
        },
        {
          key: 'sales-clientes',
          label: <Link to="/sales/clientes">Catálogo de Clientes</Link>,
        },
        {
          key: 'sales-orders',
          label: <Link to="/sales/orders">Cotizaciones y Órdenes</Link>,
        },
        {
          key: 'sales-products',
          label: <Link to="/sales/products">Catálogo de Productos</Link>,
        },
        {
          key: 'sales-reportes-menu',
          label: 'Reportes',
          children: [
            { key: 'rep-ventas', label: <Link to="/sales/reports?tab=ventas">Ventas</Link> },
            { key: 'rep-vendedores', label: <Link to="/sales/reports?tab=vendedores">Vendedores</Link> },
            { key: 'rep-productos', label: <Link to="/sales/reports?tab=productos">Productos</Link> },
            { key: 'rep-clientes', label: <Link to="/sales/reports?tab=clientes">Clientes</Link> },
          ]
        },
        {
          key: 'sales-config-menu',
          label: 'Configuración',
          children: [
            { key: 'cfg-ajustes', label: <Link to="/sales/config?tab=ajustes">Ajustes</Link> },
            { key: 'cfg-equipos', label: <Link to="/sales/config?tab=equipos">Equipos de ventas</Link> },
            { key: 'cfg-ordenes', label: <Link to="/sales/config?tab=ordenes">Órdenes de venta</Link> },
            { key: 'cfg-encabezados', label: <Link to="/sales/config?tab=encabezados">Encabezados/pies</Link> },
            { key: 'cfg-etiquetas', label: <Link to="/sales/config?tab=etiquetas">Etiquetas</Link> },
            { key: 'cfg-combos', label: <Link to="/sales/config?tab=combos">Opciones de combos</Link> },
            { key: 'cfg-pagos-online', label: <Link to="/sales/config?tab=pagos">Pagos en línea</Link> },
            { key: 'cfg-metodos-pago', label: <Link to="/sales/config?tab=metodos">Métodos de pago</Link> },
            { key: 'cfg-actividades', label: <Link to="/sales/config?tab=actividades">Actividades y Planes</Link> },
          ]
        }
      ]
    },
    {
      key: 'purchases',
      icon: <TeamOutlined />,
      label: 'Compras (CxP)',
      hidden: !tenantUser,
      children: [
        {
          key: 'purchases-orders',
          label: <Link to="/purchases/orders">Órdenes de Compra</Link>,
        },
        {
          key: 'purchases-proveedores',
          label: <Link to="/purchases/proveedores">Proveedores</Link>,
        }
      ]
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
            justifyContent: 'flex-end',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <SkinOutlined style={{ marginRight: 8 }} />
            <span>Tema:</span>
            <div style={{ marginLeft: 8, marginRight: 24 }}>
              <Switch 
                checked={darkMode} 
                onChange={setDarkMode} 
                checkedChildren="Oscuro"
                unCheckedChildren="Claro"
              />
            </div>
            <UserOutlined style={{ marginRight: 8 }} />
            <span style={{ marginRight: 16 }}>
              {user?.nombre_completo || user?.email || 'Usuario'}
            </span>
            <Button 
              type="primary" 
              danger 
              onClick={() => {
                store.dispatch({ type: 'auth/logout' });
                window.location.href = '/login';
              }}
            >
              Cerrar Sesión
            </Button>
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
          <Route path="/finance/cxc" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <AccountsReceivable />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/cxp" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <AccountsPayable />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/expenses" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ExpensesDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <AccountingDashboard />
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
          <Route path="/finance/dashboard" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <AccountingDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/cuentas" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ChartOfAccounts />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/polizas" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <JournalEntries />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/journal" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <JournalAudit />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/aging" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <AgingReports />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/treasury" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <TreasuryDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/transactions" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <BankTransactions />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/finance/settings" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <AccountingSettings />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/dashboard" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <InventoryDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/productos" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ProductsList />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/movements" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <StockMovements />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/physical" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <PhysicalInventory />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/config" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <ConfiguracionInventario />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/inventory/traceability" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <TrazabilidadVisor />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/production/dashboard" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ProductionDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/production/orders" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ProductionOrders />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/production/proyectos" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ProyectosProduccion />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/dashboard" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <SalesDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/reports" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <SalesReports />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/clientes" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <Clientes />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/orders" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <SalesOrders />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/products" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <ProductsList />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/config" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <SalesConfig />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/pos" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <PointOfSale />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales/history" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <SalesHistory />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/sales-b2b" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa', 'cliente_b2b']}>
                <B2BDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />

          {/* HR Routes */}
          <Route path="/hr" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <HRDashboard />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/directory" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <EmployeeDirectory />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/timeoff" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <TimeOff />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/checador" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <Checador />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/payroll" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <Payroll />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/payroll-config" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <PayrollConfig />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/hr/fiscal-config" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['admin', 'admin_empresa']}>
                <FiscalConfig />
              </ProtectedRoute>
            </MainLayout>
          } />

          <Route path="/purchases/orders" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <PurchaseOrders />
              </ProtectedRoute>
            </MainLayout>
          } />
          <Route path="/purchases/proveedores" element={
            <MainLayout>
              <ProtectedRoute allowedRoles={['user', 'normal', 'admin', 'admin_empresa']}>
                <Proveedores />
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
