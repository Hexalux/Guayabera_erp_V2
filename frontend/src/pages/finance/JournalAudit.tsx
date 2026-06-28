import React, { useState, useEffect } from 'react';
import { Card, Table, Typography, Tag, Space, message, Collapse } from 'antd';
import { SafetyCertificateOutlined, CodeSandboxOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Panel } = Collapse;

export const JournalAudit: React.FC = () => {
  const [polizas, setPolizas] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPolizas();
  }, []);

  const fetchPolizas = async () => {
    setLoading(true);
    try {
      const res = await api.get('/accounting/journal');
      setPolizas(res.data);
    } catch (error) {
      message.error('Error al cargar pólizas de diario');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { 
      title: 'Poliza #', 
      dataIndex: 'numero', 
      key: 'numero', 
      render: (n: number, record: any) => <Tag color="blue">{record.tipo.toUpperCase()}-{n}</Tag> 
    },
    { 
      title: 'Fecha', 
      dataIndex: 'fecha', 
      key: 'fecha', 
      render: (d: string) => dayjs(d).format('DD/MM/YYYY') 
    },
    { 
      title: 'Descripción (Concepto General)', 
      dataIndex: 'descripcion', 
      key: 'descripcion' 
    },
    { 
      title: 'Cargos', 
      dataIndex: 'total_cargos', 
      key: 'cargos', 
      align: 'right' as const,
      render: (v: number) => <Text style={{ color: '#DAA520' }}>${v.toFixed(2)}</Text> 
    },
    { 
      title: 'Abonos', 
      dataIndex: 'total_abonos', 
      key: 'abonos', 
      align: 'right' as const,
      render: (v: number) => <Text style={{ color: '#00A651' }}>${v.toFixed(2)}</Text> 
    },
    { 
      title: 'Cuadre', 
      key: 'cuadre', 
      align: 'center' as const,
      render: (_: any, record: any) => (
        record.total_cargos === record.total_abonos 
          ? <Tag color="success">CUADRADO</Tag> 
          : <Tag color="error">DESCUADRE</Tag>
      )
    }
  ];

  const expandedRowRender = (record: any) => {
    const movCols = [
      { title: 'Cuenta', dataIndex: 'cuenta_codigo', key: 'cta', width: '15%' },
      { title: 'Nombre', dataIndex: 'cuenta_nombre', key: 'nombre' },
      { title: 'Concepto', dataIndex: 'concepto', key: 'concepto' },
      { title: 'Cargo', dataIndex: 'cargo', key: 'cargo', align: 'right' as const, render: (v: number) => v > 0 ? `$${v.toFixed(2)}` : '-' },
      { title: 'Abono', dataIndex: 'abono', key: 'abono', align: 'right' as const, render: (v: number) => v > 0 ? `$${v.toFixed(2)}` : '-' },
    ];

    return (
      <Table 
        columns={movCols} 
        dataSource={record.movimientos} 
        pagination={false} 
        rowKey="id"
        size="small"
        style={{ margin: '16px 0' }}
      />
    );
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Title level={2} style={{ color: '#2196F3', marginBottom: '8px' }}>
        <SafetyCertificateOutlined /> Auditoría de Diario (Libro Diario)
      </Title>
      <Text style={{ color: '#B8B9BD', display: 'block', marginBottom: '24px' }}>
        Trazabilidad inmutable de todos los apuntes contables generados por el ERP.
      </Text>

      <Card 
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={polizas} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          expandable={{ expandedRowRender }}
          pagination={{ pageSize: 15 }}
          className="dark-table"
        />
      </Card>
      
      <style>{`
        .dark-table .ant-table { background-color: transparent !important; color: #FFF !important; }
        .dark-table .ant-table-thead > tr > th { background-color: #0C0E14 !important; color: #B8B9BD !important; border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid #303030; }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: #0C0E14 !important; }
        .dark-table .ant-table-expanded-row > td { background-color: #0F121A !important; }
        .ant-table-pagination.ant-pagination { margin: 16px !important; }
      `}</style>
    </div>
  );
};
