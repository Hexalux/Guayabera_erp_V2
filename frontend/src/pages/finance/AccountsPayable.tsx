import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Table, Typography, Space, Tag, Modal, InputNumber, Select, message, Statistic } from 'antd';
import { ShopOutlined, DollarOutlined, BankOutlined, SyncOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;
const { Option } = Select;

interface CxP {
  id: string;
  proveedor_nombre: string;
  folio_orden: string;
  monto_original: number;
  monto_pagado: number;
  saldo_pendiente: number;
  fecha_emision: string;
  fecha_vencimiento: string;
  estado: string;
}

export const AccountsPayable: React.FC = () => {
  const [cxpList, setCxpList] = useState<CxP[]>([]);
  const [bancos, setBancos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modal State
  const [isPaymentModalVisible, setIsPaymentModalVisible] = useState(false);
  const [selectedCxp, setSelectedCxp] = useState<CxP | null>(null);
  const [paymentData, setPaymentData] = useState({ cuenta_bancaria_id: '', monto: 0, referencia: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resCxp, resBancos] = await Promise.all([
        api.get('/purchases/cxp/saldos'),
        api.get('/treasury/accounts')
      ]);
      setCxpList(resCxp.data);
      setBancos(resBancos.data);
    } catch (error) {
      console.error('Error fetching CxP', error);
      message.error('Error al cargar pasivos');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPayment = (cxp: CxP) => {
    setSelectedCxp(cxp);
    setPaymentData({ cuenta_bancaria_id: '', monto: cxp.saldo_pendiente, referencia: '' });
    setIsPaymentModalVisible(true);
  };

  const handleProcessPayment = async () => {
    if (!selectedCxp) return;
    try {
      await api.post('/purchases/cxp/pagar', {
        cuenta_por_pagar_id: selectedCxp.id,
        ...paymentData
      });
      message.success('Pago emitido y contabilizado exitosamente.');
      setIsPaymentModalVisible(false);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al procesar pago');
    }
  };

  const totalPorPagar = cxpList.reduce((sum, c) => sum + c.saldo_pendiente, 0);

  const columns = [
    { 
      title: 'Proveedor', 
      dataIndex: 'proveedor_nombre', 
      key: 'proveedor',
      render: (text: string) => <Text strong style={{ color: '#DAA520' }}>{text}</Text>
    },
    { 
      title: 'Folio OC', 
      dataIndex: 'folio_orden', 
      key: 'folio',
      render: (text: string) => <Tag color="purple">{text}</Tag>
    },
    { 
      title: 'Estado', 
      dataIndex: 'estado', 
      key: 'estado',
      render: (text: string) => (
        <Tag color={text === 'pagada' ? 'success' : text === 'pendiente' ? 'error' : 'warning'}>
          {text.toUpperCase()}
        </Tag>
      )
    },
    { 
      title: 'Vencimiento', 
      dataIndex: 'fecha_vencimiento', 
      key: 'vencimiento',
      render: (text: string) => <Text style={{ color: '#B8B9BD' }}>{new Date(text).toLocaleDateString()}</Text>
    },
    { 
      title: 'Pagado', 
      dataIndex: 'monto_pagado', 
      key: 'pagado',
      render: (val: number) => <Text style={{ color: '#00A651' }}>${val.toFixed(2)}</Text>
    },
    { 
      title: 'Saldo Pendiente', 
      dataIndex: 'saldo_pendiente', 
      key: 'saldo',
      render: (val: number) => <Text strong style={{ color: '#F44336', fontSize: '16px' }}>${val.toFixed(2)}</Text>
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: CxP) => (
        <Space>
          {record.saldo_pendiente > 0 && (
            <Button 
              size="small" 
              style={{ backgroundColor: '#0C0E14', color: '#DAA520', borderColor: '#DAA520' }}
              icon={<DollarOutlined />}
              onClick={() => handleOpenPayment(record)}
            >
              Pagar Factura
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
          <Title level={2} style={{ color: '#F44336', margin: 0 }}>
            <ShopOutlined /> Cuentas por Pagar
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Gestión de obligaciones y pagos a proveedores</Text>
        </Col>
        <Col>
          <Button icon={<SyncOutlined />} onClick={fetchData} loading={loading}>
            Actualizar
          </Button>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} md={8}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic 
              title={<Text style={{ color: '#B8B9BD' }}>Pasivo Circulante Total (Deuda)</Text>}
              value={totalPorPagar} 
              precision={2} 
              prefix="$" 
              valueStyle={{ color: '#F44336', fontWeight: 'bold' }} 
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={<Text style={{ color: '#FFF' }}><BankOutlined /> Obligaciones de Pago</Text>}
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={cxpList} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          className="dark-table"
        />
      </Card>

      {/* Modal Emitir Pago */}
      <Modal
        title={`Pagar a ${selectedCxp?.proveedor_nombre}`}
        open={isPaymentModalVisible}
        onOk={handleProcessPayment}
        onCancel={() => setIsPaymentModalVisible(false)}
        okText="Emitir Pago"
        cancelText="Cancelar"
        okButtonProps={{ danger: true }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Deuda Pendiente: <strong style={{ color: '#F44336' }}>${selectedCxp?.saldo_pendiente.toFixed(2)}</strong></Text>
          
          <Select 
            style={{ width: '100%' }}
            placeholder="Seleccione cuenta bancaria de origen"
            value={paymentData.cuenta_bancaria_id}
            onChange={(val) => setPaymentData({...paymentData, cuenta_bancaria_id: val})}
          >
            {bancos.map(b => (
              <Option key={b.id} value={b.id}>
                <span style={{ color: b.saldo_actual >= paymentData.monto ? '#000' : 'red' }}>
                  {b.banco} - {b.numero_cuenta} (Saldo: ${b.saldo_actual})
                </span>
              </Option>
            ))}
          </Select>

          <InputNumber 
            style={{ width: '100%' }}
            placeholder="Monto a Pagar" 
            prefix="$"
            min={0.01}
            max={selectedCxp?.saldo_pendiente}
            value={paymentData.monto}
            onChange={val => setPaymentData({...paymentData, monto: val || 0})}
          />
        </Space>
      </Modal>

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
      `}</style>
    </div>
  );
};
