import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Table, Typography, Space, Tag, Modal, InputNumber, Select, message, Statistic } from 'antd';
import { UserOutlined, DollarOutlined, CreditCardOutlined, SyncOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;
const { Option } = Select;

interface CxC {
  id: string;
  cliente_nombre: string;
  folio_venta: string;
  monto_original: number;
  saldo_pendiente: number;
  fecha_emision: string;
  fecha_vencimiento: string;
  estado: string;
}

export const AccountsReceivable: React.FC = () => {
  const [cxcList, setCxcList] = useState<CxC[]>([]);
  const [bancos, setBancos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modal State
  const [isPaymentModalVisible, setIsPaymentModalVisible] = useState(false);
  const [selectedCxc, setSelectedCxc] = useState<CxC | null>(null);
  const [paymentData, setPaymentData] = useState({ cuenta_bancaria_id: '', monto: 0, referencia: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resCxc, resBancos] = await Promise.all([
        api.get('/cxc/saldos'),
        api.get('/treasury/accounts')
      ]);
      setCxcList(resCxc.data);
      setBancos(resBancos.data);
    } catch (error) {
      console.error('Error fetching CxC', error);
      message.error('Error al cargar saldos');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPayment = (cxc: CxC) => {
    setSelectedCxc(cxc);
    setPaymentData({ cuenta_bancaria_id: '', monto: cxc.saldo_pendiente, referencia: '' });
    setIsPaymentModalVisible(true);
  };

  const handleProcessPayment = async () => {
    if (!selectedCxc) return;
    try {
      await api.post('/cxc/pagar', {
        cuenta_por_cobrar_id: selectedCxc.id,
        ...paymentData
      });
      message.success('Pago aplicado y contabilizado exitosamente.');
      setIsPaymentModalVisible(false);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al procesar pago');
    }
  };

  const totalPorCobrar = cxcList.reduce((sum, c) => sum + c.saldo_pendiente, 0);

  const columns = [
    { 
      title: 'Cliente', 
      dataIndex: 'cliente_nombre', 
      key: 'cliente',
      render: (text: string) => <Text strong style={{ color: '#00A651' }}>{text}</Text>
    },
    { 
      title: 'Folio Venta', 
      dataIndex: 'folio_venta', 
      key: 'folio',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    { 
      title: 'Estado', 
      dataIndex: 'estado', 
      key: 'estado',
      render: (text: string) => (
        <Tag color={text === 'pagada' ? 'success' : text === 'vencida' ? 'error' : 'warning'}>
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
      title: 'Saldo Pendiente', 
      dataIndex: 'saldo_pendiente', 
      key: 'saldo',
      render: (val: number) => <Text strong style={{ color: '#DAA520', fontSize: '16px' }}>${val.toFixed(2)}</Text>
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: CxC) => (
        <Space>
          {record.saldo_pendiente > 0 && (
            <Button 
              size="small" 
              style={{ backgroundColor: '#0C0E14', color: '#00A651', borderColor: '#00A651' }}
              icon={<DollarOutlined />}
              onClick={() => handleOpenPayment(record)}
            >
              Cobrar
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
          <Title level={2} style={{ color: '#DAA520', margin: 0 }}>
            <UserOutlined /> Cuentas por Cobrar
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Gestión de cobranza a clientes</Text>
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
              title={<Text style={{ color: '#B8B9BD' }}>Total Cartera Vencida/Vigente</Text>}
              value={totalPorCobrar} 
              precision={2} 
              prefix="$" 
              valueStyle={{ color: '#F44336', fontWeight: 'bold' }} 
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={<Text style={{ color: '#FFF' }}><CreditCardOutlined /> Cartera de Clientes</Text>}
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={cxcList} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          className="dark-table"
        />
      </Card>

      {/* Modal Aplicar Pago */}
      <Modal
        title={`Cobrar a ${selectedCxc?.cliente_nombre}`}
        open={isPaymentModalVisible}
        onOk={handleProcessPayment}
        onCancel={() => setIsPaymentModalVisible(false)}
        okText="Aplicar Cobro"
        cancelText="Cancelar"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Deuda Total: <strong>${selectedCxc?.saldo_pendiente.toFixed(2)}</strong></Text>
          
          <Select 
            style={{ width: '100%' }}
            placeholder="Seleccione cuenta bancaria destino"
            value={paymentData.cuenta_bancaria_id}
            onChange={(val) => setPaymentData({...paymentData, cuenta_bancaria_id: val})}
          >
            {bancos.map(b => (
              <Option key={b.id} value={b.id}>{b.banco} - {b.numero_cuenta} (${b.saldo_actual})</Option>
            ))}
          </Select>

          <InputNumber 
            style={{ width: '100%' }}
            placeholder="Monto a Cobrar" 
            prefix="$"
            min={0.01}
            max={selectedCxc?.saldo_pendiente}
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
