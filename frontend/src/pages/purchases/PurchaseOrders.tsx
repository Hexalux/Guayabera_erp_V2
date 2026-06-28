import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Table, Typography, Space, Tag, message, Modal } from 'antd';
import { ShoppingOutlined, PlusOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;

interface Proveedor {
  id: string;
  razon_social: string;
}

interface OrdenCompra {
  id: string;
  folio: string;
  fecha_emision: string;
  fecha_recepcion: string | null;
  estado: string;
  total: number;
  proveedor_id: string;
}

export const PurchaseOrders: React.FC = () => {
  const [ordenes, setOrdenes] = useState<OrdenCompra[]>([]);
  const [proveedores, setProveedores] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [receivingId, setReceivingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ordRes, provRes] = await Promise.all([
        api.get('/purchases/ordenes'),
        api.get('/purchases/proveedores')
      ]);
      
      setOrdenes(ordRes.data);
      
      const provMap: Record<string, string> = {};
      provRes.data.forEach((p: Proveedor) => {
        provMap[p.id] = p.razon_social;
      });
      setProveedores(provMap);
      
    } catch (error) {
      console.error('Error fetching purchases data', error);
      message.error('No se pudieron cargar las órdenes de compra.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecibir = async (id: string) => {
    setReceivingId(id);
    try {
      const res = await api.post(`/purchases/ordenes/${id}/recibir`);
      message.success(res.data.mensaje || 'Mercancía recibida correctamente.');
      fetchData(); // Recargar
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al recibir la orden.');
    } finally {
      setReceivingId(null);
    }
  };

  const handleConfirmarRFQ = async (id: string) => {
    setConfirmingId(id);
    try {
      const res = await api.post(`/purchases/ordenes/${id}/confirmar`);
      message.success(res.data.mensaje || 'RFQ confirmado y emitido.');
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al confirmar el RFQ.');
    } finally {
      setConfirmingId(null);
    }
  };

  const columns = [
    { 
      title: 'Folio', 
      dataIndex: 'folio', 
      key: 'folio',
      render: (text: string) => <Text strong style={{ color: '#00A651' }}>{text}</Text>
    },
    { 
      title: 'Proveedor', 
      key: 'proveedor',
      render: (_: any, record: OrdenCompra) => <Text style={{ color: '#FFF' }}>{proveedores[record.proveedor_id] || 'Desconocido'}</Text>
    },
    { 
      title: 'Fecha Emisión', 
      dataIndex: 'fecha_emision', 
      key: 'fecha_emision',
      render: (val: string) => new Date(val).toLocaleDateString()
    },
    { 
      title: 'Total', 
      dataIndex: 'total', 
      key: 'total',
      render: (val: number) => <Text style={{ color: '#DAA520' }}>${val.toFixed(2)}</Text>
    },
    { 
      title: 'Estado', 
      dataIndex: 'estado', 
      key: 'estado',
      render: (estado: string) => {
        let color = 'processing';
        if (estado === 'rfq') color = 'warning';
        if (estado === 'emitida') color = 'processing';
        if (estado === 'recibida') color = 'success';
        if (estado === 'cancelada') color = 'error';
        return <Tag color={color}>{estado.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: OrdenCompra) => (
        <Space>
          {record.estado === 'rfq' && (
            <Button 
              type="primary" 
              icon={<CheckCircleOutlined />} 
              size="small"
              loading={confirmingId === record.id}
              onClick={() => handleConfirmarRFQ(record.id)}
              style={{ backgroundColor: '#DAA520', borderColor: '#DAA520' }}
            >
              Confirmar (Emitir OC)
            </Button>
          )}
          {record.estado === 'emitida' && (
            <Button 
              type="primary" 
              icon={<CheckCircleOutlined />} 
              size="small"
              loading={receivingId === record.id}
              onClick={() => handleRecibir(record.id)}
              style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
            >
              Recibir Mercancía
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: '#00A651', margin: 0 }}>
            <ShoppingOutlined /> Órdenes de Compra
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Gestión de Cadena de Abastecimiento y Cuentas por Pagar</Text>
        </Col>
        <Col>
          <Space>
            <Button icon={<SyncOutlined />} onClick={fetchData} loading={loading}>
              Actualizar
            </Button>
            <Button type="primary" icon={<PlusOutlined />} style={{ backgroundColor: '#DAA520', borderColor: '#DAA520' }}>
              Nueva Orden
            </Button>
          </Space>
        </Col>
      </Row>

      <Card 
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={ordenes} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          className="dark-table"
        />
      </Card>

      <style>{`
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
        .dark-table .ant-pagination-item-active {
          background-color: #00A651 !important;
          border-color: #00A651 !important;
        }
        .dark-table .ant-pagination-item-active a {
          color: #FFF !important;
        }
      `}</style>
    </div>
  );
};
