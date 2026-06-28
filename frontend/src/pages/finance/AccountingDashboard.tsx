import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Table, Spin, Statistic, message } from 'antd';
import { AreaChartOutlined, DollarOutlined, BankOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;

export const AccountingDashboard: React.FC = () => {
  const [balance, setBalance] = useState<any>(null);
  const [pl, setPl] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resBalance, resPl] = await Promise.all([
        api.get('/accounting/reports/balance-general'),
        api.get('/accounting/reports/estado-resultados')
      ]);
      setBalance(resBalance.data);
      setPl(resPl.data);
    } catch (error) {
      message.error('Error al cargar reportes financieros');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: 'Código', dataIndex: 'codigo', key: 'codigo', width: '20%' },
    { title: 'Cuenta', dataIndex: 'nombre', key: 'nombre' },
    { 
      title: 'Saldo', 
      dataIndex: 'saldo', 
      key: 'saldo', 
      align: 'right' as const,
      render: (v: number) => (
        <Text style={{ color: v >= 0 ? '#FFF' : '#F44336', fontWeight: 500 }}>
          ${v.toFixed(2)}
        </Text>
      )
    }
  ];

  if (loading || !balance || !pl) {
    return <div style={{ textAlign: 'center', marginTop: '100px' }}><Spin size="large" /></div>;
  }

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Title level={2} style={{ color: '#DAA520', marginBottom: '24px' }}>
        <AreaChartOutlined /> Inteligencia Financiera (Reportes Oficiales)
      </Title>

      {/* KPIs Rápidos */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic 
              title={<span style={{ color: '#B8B9BD' }}>Activos Totales</span>} 
              value={balance.activos.total} 
              precision={2} 
              prefix={<BankOutlined />} 
              valueStyle={{ color: '#2196F3' }} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic 
              title={<span style={{ color: '#B8B9BD' }}>Utilidad Neta (P&L)</span>} 
              value={pl.utilidad_neta} 
              precision={2} 
              prefix={<DollarOutlined />} 
              valueStyle={{ color: pl.utilidad_neta >= 0 ? '#00A651' : '#F44336' }} 
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* Balance General */}
        <Col xs={24} lg={12}>
          <Card 
            title={<Text style={{ color: '#FFF', fontSize: '18px' }}>Balance General (Estado de Situación Financiera)</Text>}
            style={{ backgroundColor: '#161A24', borderColor: '#303030', height: '100%' }}
            headStyle={{ borderBottomColor: '#303030' }}
            bodyStyle={{ padding: 0 }}
          >
            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030' }}>
              <Text strong style={{ color: '#2196F3' }}>1. ACTIVOS</Text>
              <span style={{ float: 'right', color: '#2196F3', fontWeight: 'bold' }}>${balance.activos.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={balance.activos.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />
            
            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030', borderTop: '1px solid #303030' }}>
              <Text strong style={{ color: '#F44336' }}>2. PASIVOS</Text>
              <span style={{ float: 'right', color: '#F44336', fontWeight: 'bold' }}>${balance.pasivos.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={balance.pasivos.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />

            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030', borderTop: '1px solid #303030' }}>
              <Text strong style={{ color: '#DAA520' }}>3. CAPITAL</Text>
              <span style={{ float: 'right', color: '#DAA520', fontWeight: 'bold' }}>${balance.capital.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={balance.capital.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />
            
            <div style={{ padding: '16px', textAlign: 'center' }}>
              <Text style={{ color: balance.ecuacion_contable ? '#00A651' : '#F44336' }}>
                {balance.ecuacion_contable ? '✅ Cuadrado (Activo = Pasivo + Capital)' : '❌ Descuadre Detectado'}
              </Text>
            </div>
          </Card>
        </Col>

        {/* Estado de Resultados */}
        <Col xs={24} lg={12}>
          <Card 
            title={<Text style={{ color: '#FFF', fontSize: '18px' }}>Estado de Resultados (P&L)</Text>}
            style={{ backgroundColor: '#161A24', borderColor: '#303030', height: '100%' }}
            headStyle={{ borderBottomColor: '#303030' }}
            bodyStyle={{ padding: 0 }}
          >
            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030' }}>
              <Text strong style={{ color: '#00A651' }}>4. INGRESOS</Text>
              <span style={{ float: 'right', color: '#00A651', fontWeight: 'bold' }}>${pl.ingresos.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={pl.ingresos.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />
            
            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030', borderTop: '1px solid #303030' }}>
              <Text strong style={{ color: '#DAA520' }}>5. COSTOS DE VENTA</Text>
              <span style={{ float: 'right', color: '#DAA520', fontWeight: 'bold' }}>${pl.costos.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={pl.costos.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />

            <div style={{ padding: '16px', backgroundColor: '#161A24', borderBottom: '1px solid #303030' }}>
              <Text strong>UTILIDAD BRUTA</Text>
              <span style={{ float: 'right', fontWeight: 'bold' }}>${pl.utilidad_bruta.toFixed(2)}</span>
            </div>

            <div style={{ padding: '16px', backgroundColor: '#0C0E14', borderBottom: '1px solid #303030' }}>
              <Text strong style={{ color: '#F44336' }}>6. GASTOS DE OPERACIÓN</Text>
              <span style={{ float: 'right', color: '#F44336', fontWeight: 'bold' }}>${pl.gastos.total.toFixed(2)}</span>
            </div>
            <Table 
              dataSource={pl.gastos.cuentas.filter((c: any) => c.saldo !== 0)} 
              columns={columns} 
              rowKey="id" 
              pagination={{ pageSize: 5 }} 
              className="dark-table" 
              size="small"
            />
            
            <div style={{ padding: '20px', backgroundColor: pl.utilidad_neta >= 0 ? 'rgba(0, 166, 81, 0.1)' : 'rgba(244, 67, 54, 0.1)', textAlign: 'right' }}>
              <Title level={4} style={{ color: pl.utilidad_neta >= 0 ? '#00A651' : '#F44336', margin: 0 }}>
                UTILIDAD NETA: ${pl.utilidad_neta.toFixed(2)}
              </Title>
            </div>
          </Card>
        </Col>
      </Row>

      <style>{`
        .dark-table .ant-table { background-color: transparent !important; color: #FFF !important; }
        .dark-table .ant-table-thead > tr > th { background-color: #0C0E14 !important; color: #B8B9BD !important; border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: #0C0E14 !important; }
        .ant-table-pagination.ant-pagination { margin: 16px !important; }
      `}</style>
    </div>
  );
};
