import React, { useState, useEffect } from 'react';
import { Card, Table, Typography, message, Tag } from 'antd';
import { HistoryOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import { salesService, VentaPOS } from '../../services/salesService';

const { Title, Text } = Typography;

export const SalesHistory: React.FC = () => {
  const [ventas, setVentas] = useState<VentaPOS[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchVentas();
  }, []);

  const fetchVentas = async () => {
    setLoading(true);
    try {
      const res = await salesService.getVentasPOS();
      setVentas(res);
    } catch (error) {
      message.error('Error al cargar historial de ventas');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: 'Folio', dataIndex: 'folio', key: 'folio', render: (t: string) => <Tag color="blue">{t}</Tag> },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (t: string) => new Date(t).toLocaleString() },
    { title: 'Total', dataIndex: 'total', key: 'total', render: (v: number) => <Text style={{ color: '#00A651' }}>${v.toFixed(2)}</Text> },
    { title: 'Método de Pago', dataIndex: 'metodo_pago', key: 'metodo', render: (t: string) => <Tag color="purple">{t}</Tag> }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Title level={2} style={{ color: '#00A651', marginBottom: '24px' }}>
        <HistoryOutlined /> Historial de Ventas POS
      </Title>
      
      <Card 
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={ventas} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
          className="dark-table"
        />
      </Card>
      
      <style>{`
        .dark-table .ant-table { background-color: transparent !important; color: #FFF !important; }
        .dark-table .ant-table-thead > tr > th { background-color: #0C0E14 !important; color: #B8B9BD !important; border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: #0C0E14 !important; }
      `}</style>
    </div>
  );
};
