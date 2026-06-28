import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Table, Spin, Tabs, Tag, message } from 'antd';
import { ClockCircleOutlined, FallOutlined, RiseOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export const AgingReports: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAging();
  }, []);

  const fetchAging = async () => {
    setLoading(true);
    try {
      const res = await api.get('/accounting/reports/aging');
      setData(res.data);
    } catch (error) {
      message.error('Error al cargar reporte de antigüedad de saldos');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (val: number) => `$${val.toFixed(2)}`;

  const getBucketColor = (bucket: string) => {
    switch(bucket) {
      case 'current': return 'green';
      case '30_days': return 'gold';
      case '60_days': return 'orange';
      case '90_days': return 'volcano';
      case 'older': return 'red';
      default: return 'default';
    }
  };

  const columns = [
    { title: 'Documento', dataIndex: 'documento', key: 'doc' },
    { title: 'Entidad', dataIndex: 'entidad', key: 'entidad' },
    { 
      title: 'Vencimiento', 
      dataIndex: 'fecha_vencimiento', 
      key: 'venc',
      render: (d: string) => dayjs(d).format('DD/MM/YYYY')
    },
    { 
      title: 'Días Vencido', 
      dataIndex: 'dias_vencido', 
      key: 'dias',
      align: 'center' as const,
      render: (v: number) => (
        <Text style={{ color: v > 0 ? '#F44336' : '#00A651' }}>
          {v === 0 ? 'Al corriente' : `${v} días`}
        </Text>
      )
    },
    { 
      title: 'Antigüedad', 
      dataIndex: 'bucket', 
      key: 'bucket',
      align: 'center' as const,
      render: (v: string) => <Tag color={getBucketColor(v)}>{v.toUpperCase()}</Tag>
    },
    { 
      title: 'Saldo Pendiente', 
      dataIndex: 'saldo', 
      key: 'saldo',
      align: 'right' as const,
      render: (v: number) => <Text strong>{formatCurrency(v)}</Text>
    }
  ];

  if (loading || !data) {
    return <div style={{ textAlign: 'center', marginTop: '100px' }}><Spin size="large" /></div>;
  }

  const SummaryCards = ({ summary, type }: { summary: any, type: 'cxc' | 'cxp' }) => (
    <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#161A24', borderColor: '#00A651' }}>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>Al Corriente</Text>
          <Title level={4} style={{ color: '#00A651', margin: 0 }}>{formatCurrency(summary.current)}</Title>
        </Card>
      </Col>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#161A24', borderColor: '#DAA520' }}>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>1 - 30 Días</Text>
          <Title level={4} style={{ color: '#DAA520', margin: 0 }}>{formatCurrency(summary.days_30)}</Title>
        </Card>
      </Col>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#161A24', borderColor: '#FF9800' }}>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>31 - 60 Días</Text>
          <Title level={4} style={{ color: '#FF9800', margin: 0 }}>{formatCurrency(summary.days_60)}</Title>
        </Card>
      </Col>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#161A24', borderColor: '#FF5722' }}>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>61 - 90 Días</Text>
          <Title level={4} style={{ color: '#FF5722', margin: 0 }}>{formatCurrency(summary.days_90)}</Title>
        </Card>
      </Col>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#161A24', borderColor: '#F44336' }}>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>+90 Días</Text>
          <Title level={4} style={{ color: '#F44336', margin: 0 }}>{formatCurrency(summary.older)}</Title>
        </Card>
      </Col>
      <Col span={4}>
        <Card size="small" style={{ backgroundColor: '#0C0E14', borderColor: type === 'cxc' ? '#2196F3' : '#F44336' }}>
          <Text style={{ color: '#FFF', fontSize: '12px' }}>TOTAL {type.toUpperCase()}</Text>
          <Title level={4} style={{ color: type === 'cxc' ? '#2196F3' : '#F44336', margin: 0 }}>
            {formatCurrency(summary.total)}
          </Title>
        </Card>
      </Col>
    </Row>
  );

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Title level={2} style={{ color: '#2196F3', marginBottom: '8px' }}>
        <ClockCircleOutlined /> Reporte de Antigüedad de Saldos (Aging)
      </Title>
      <Text style={{ color: '#B8B9BD', display: 'block', marginBottom: '24px' }}>
        Identifica rápidamente cuentas vencidas y flujos de efectivo en riesgo.
      </Text>

      <Tabs 
        defaultActiveKey="1" 
        type="card"
        className="dark-tabs"
        items={[
          {
            key: '1',
            label: <span><RiseOutlined /> Cuentas por Cobrar (Clientes)</span>,
            children: (
              <>
                <SummaryCards summary={data.cxc.summary} type="cxc" />
                <Card bodyStyle={{ padding: 0 }} style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
                  <Table 
                    dataSource={data.cxc.details} 
                    columns={columns} 
                    rowKey="id" 
                    className="dark-table"
                    pagination={{ pageSize: 15 }}
                  />
                </Card>
              </>
            )
          },
          {
            key: '2',
            label: <span><FallOutlined /> Cuentas por Pagar (Proveedores)</span>,
            children: (
              <>
                <SummaryCards summary={data.cxp.summary} type="cxp" />
                <Card bodyStyle={{ padding: 0 }} style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
                  <Table 
                    dataSource={data.cxp.details} 
                    columns={columns} 
                    rowKey="id" 
                    className="dark-table"
                    pagination={{ pageSize: 15 }}
                  />
                </Card>
              </>
            )
          }
        ]}
      />

      <style>{`
        .dark-tabs .ant-tabs-nav::before { border-bottom: 1px solid #303030; }
        .dark-tabs .ant-tabs-tab { background-color: #0C0E14 !important; border-color: #303030 !important; color: #B8B9BD !important; }
        .dark-tabs .ant-tabs-tab-active { background-color: #161A24 !important; border-bottom-color: #161A24 !important; }
        .dark-tabs .ant-tabs-tab-active .ant-tabs-tab-btn { color: #2196F3 !important; }
        
        .dark-table .ant-table { background-color: transparent !important; color: #FFF !important; }
        .dark-table .ant-table-thead > tr > th { background-color: #0C0E14 !important; color: #B8B9BD !important; border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: #0C0E14 !important; }
        .ant-table-pagination.ant-pagination { margin: 16px !important; }
      `}</style>
    </div>
  );
};
