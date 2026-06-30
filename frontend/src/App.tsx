
import React from 'react';
import { Admin, Resource, CustomRoutes } from 'react-admin';
import { Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import authProvider from './api/authProvider';
import dataProvider from './api/dataProvider';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './components/Auth/Login';
import ForgotPassword from './components/Auth/ForgotPassword';
import ProductList from './pages/Inventory/ProductList';
import ProductionOrderList from './pages/Production/ProductionOrderList';
import TicketList from './pages/Helpdesk/TicketList';
import ReportCenter from './pages/Reports/ReportCenter';
import DashboardTextil from './pages/Textil/DashboardTextil';

const theme = createTheme({
  palette: {
    primary: { main: '#1e3a8a' },
    secondary: { main: '#14b8a6' },
  },
});

const App = () => (
  <ThemeProvider theme={theme}>
    <Admin 
      dataProvider={dataProvider} 
      authProvider={authProvider} 
      layout={Layout}
      loginPage={Login}
      dashboard={Dashboard}
    >
      <Resource name="products" list={ProductList} />
      <Resource name="production_orders" list={ProductionOrderList} />
      <Resource name="tickets" list={TicketList} />
      <Resource name="textil_dashboard" list={DashboardTextil} />
      <Resource name="reports" list={ReportCenter} />
      
      <CustomRoutes>
        <Route path="/forgot-password" element={<ForgotPassword />} />
      </CustomRoutes>
    </Admin>
  </ThemeProvider>
);

export default App;
