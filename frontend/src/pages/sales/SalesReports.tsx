import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Progress, Tabs, Typography, Space, Spin, message } from 'antd';
import { DollarOutlined, UserOutlined, ShopOutlined, TeamOutlined, ArrowUpOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { api } from '../../services/authService';

const { Title, Text } = Typography;

interface ReportData {
  total_monto: number;
  vendedores: Array<{ nombre: string; monto: number }>;
  productos: Array<{ nombre: string; cantidad: number; monto: number }>;
  clientes: Array<{ cliente: string; monto: number }>;
}

export const SalesReports: React.FC = () => {
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'ventas';
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ReportData | null>(null);

  useEffect(() => {
    fetchReportData();
  }, []);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const res = await api.get('/sales/reportes/dashboard');
      setData(res.data);
    } catch (error) {
      console.error('Error cargando reportes', error);
      message.error('No se pudieron cargar las estadísticas de ventas.');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', backgroundColor: '#0C0E14' }}>
        <Spin size="large" />
      </div>
    );
  }

  const columnsVendedores = [
    { title: 'Vendedor', dataIndex: 'nombre', key: 'nombre', render: (text: string) => <Text style={{ color: '#FFF' }}><UserOutlined style={{ marginRight: 8, color: '#DAA520' }} />{text}</Text> },
    { title: 'Total Vendido', dataIndex: 'monto', key: 'monto', render: (val: number) => <Text style={{ color: '#00A651', fontWeight: 'bold' }}>${val.toFixed(2)}</Text> },
  ];

  const columnsProductos = [
    { title: 'Producto', dataIndex: 'nombre', key: 'nombre', render: (text: string) => <Text style={{ color: '#FFF' }}><ShopOutlined style={{ marginRight: 8, color: '#DAA520' }} />{text}</Text> },
    { title: 'Cantidad Vendida', dataIndex: 'cantidad', key: 'cantidad', render: (val: number) => <Text style={{ color: '#FFF' }}>{val} pzas</Text> },
    { title: 'Monto Total', dataIndex: 'monto', key: 'monto', render: (val: number) => <Text style={{ color: '#00A651', fontWeight: 'bold' }}>${val.toFixed(2)}</Text> },
  ];

  const columnsClientes = [
    { title: 'Cliente', dataIndex: 'cliente', key: 'cliente', render: (text: string) => <Text style={{ color: '#FFF' }}><TeamOutlined style={{ marginRight: 8, color: '#DAA520' }} />{text}</Text> },
    { title: 'Total Comprado', dataIndex: 'monto', key: 'monto', render: (val: number) => <Text style={{ color: '#00A651', fontWeight: 'bold' }}>${val.toFixed(2)}</Text> },
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF', textAlign: 'left' }}>
      <Title level={2} style={{ color: '#00A651', marginBottom: '24px' }}>
        Reportes de Ventas & Rendimiento
      </Title>

      <Row gutter={24} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
            <Statistic
              title={<span style={{ color: '#B8B9BD' }}>Ventas Totales</span>}
              value={data.total_monto}
              precision={2}
              valueStyle={{ color: '#00A651' }}
              prefix={<DollarOutlined />}
              suffix={<ArrowUpOutlined style={{ fontSize: '14px', color: '#00A651' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
            <Statistic
              title={<span style={{ color: '#B8B9BD' }}>Vendedores Activos</span>}
              value={data.vendedores.length}
              valueStyle={{ color: '#DAA520' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
            <Statistic
              title={<span style={{ color: '#B8B9BD' }}>Productos Vendidos</span>}
              value={data.productos.length}
              valueStyle={{ color: '#00A651' }}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
            <Statistic
              title={<span style={{ color: '#B8B9BD' }}>Clientes Atendidos</span>}
              value={data.clientes.length}
              valueStyle={{ color: '#DAA520' }}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
        <Tabs defaultActiveKey={activeTab} className="dark-tabs">
          <Tabs.TabPane tab="Resumen Ventas" key="ventas">
            <div style={{ padding: '16px 0' }}>
              <Title level={4} style={{ color: '#FFF', marginBottom: '24px' }}>Métricas Generales de Facturación</Title>
              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Card title={<span style={{ color: '#DAA520' }}>Meta Mensual de Ventas</span>} style={{ backgroundColor: '#0C0E14', borderColor: '#303030' }}>
                    <Progress type="dashboard" percent={75} strokeColor="#00A651" trailColor="#303030" format={percent => `${percent}%`} />
                    <div style={{ marginTop: '16px' }}>
                      <Text style={{ color: '#B8B9BD' }}>Progreso hacia la meta de ventas de la sucursal.</Text>
                    </div>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card title={<span style={{ color: '#00A651' }}>Desglose por Métodos de Pago</span>} style={{ backgroundColor: '#0C0E14', borderColor: '#303030' }}>
                    <div style={{ marginBottom: '16px' }}>
                      <Text style={{ color: '#FFF' }}>Efectivo (60%)</Text>
                      <Progress percent={60} strokeColor="#00A651" trailColor="#303030" />
                    </div>
                    <div style={{ marginBottom: '16px' }}>
                      <Text style={{ color: '#FFF' }}>Tarjeta (30%)</Text>
                      <Progress percent={30} strokeColor="#DAA520" trailColor="#303030" />
                    </div>
                    <div style={{ marginBottom: '16px' }}>
                      <Text style={{ color: '#FFF' }}>Transferencia (10%)</Text>
                      <Progress percent={10} strokeColor="#2196F3" trailColor="#303030" />
                    </div>
                  </Card>
                </Col>
              </Row>
            </div>
          </Tabs.TabPane>
          <Tabs.TabPane tab="Rendimiento Vendedores" key="vendedores">
            <Table
              dataSource={data.vendedores}
              columns={columnsVendedores}
              pagination={false}
              rowKey="nombre"
              className="dark-table"
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="Top Productos" key="productos">
            <Table
              dataSource={data.productos}
              columns={columnsProductos}
              pagination={false}
              rowKey="nombre"
              className="dark-table"
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="Clientes Destacados" key="clientes">
            <Table
              dataSource={data.clientes}
              columns={columnsClientes}
              pagination={false}
              rowKey="cliente"
              className="dark-table"
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>

      <style>{`
        .dark-tabs .ant-tabs-nav {
          border-bottom: 1px solid #303030 !important;
        }
        .dark-tabs .ant-tabs-tab {
          color: #B8B9BD !important;
        }
        .dark-tabs .ant-tabs-tab-active {
          color: #00A651 !important;
        }
        .dark-tabs .ant-tabs-ink-bar {
          background-color: #00A651 !important;
        }
        .dark-table .ant-table {
          background-color: transparent !important;
          color: #FFF !important;
        }
        .dark-table .ant-table-thead > tr > th {
          background-color: #0C0E14 !important;
          color: #B8B9BD !important;
          border-bottom: 1px solid #303030;
        }
        .dark-table .ant-table-tbody > tr > td {
          border-bottom: 1px solid #303030;
        }
        .dark-table .ant-table-tbody > tr:hover > td {
          background-color: #0C0E14 !important;
        }
      `}</style>
    </div>
  );
};
