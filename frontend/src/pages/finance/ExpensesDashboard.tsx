import React, { useState, useEffect } from 'react';
import { Card, Typography, Tabs, Table, Tag, Button, Space, message, Modal, Select, Input, InputNumber, Row, Col, Statistic } from 'antd';
import { DollarOutlined, PlusOutlined, CheckCircleOutlined, SyncOutlined, BankOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface CategoriaGasto {
  id: string;
  nombre: string;
}

interface GastoOperativo {
  id: string;
  concepto: string;
  monto: number;
  fecha: string;
  estado: string;
  categoria_nombre: string;
  usuario_nombre: string;
  banco_origen?: string;
}

interface CuentaBancaria {
  id: string;
  banco: string;
  numero_cuenta: string;
  saldo_actual: number;
}

export const ExpensesDashboard: React.FC = () => {
  const [gastos, setGastos] = useState<GastoOperativo[]>([]);
  const [categorias, setCategorias] = useState<CategoriaGasto[]>([]);
  const [cuentas, setCuentas] = useState<CuentaBancaria[]>([]);
  const [loading, setLoading] = useState(false);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [newGasto, setNewGasto] = useState({ concepto: '', monto: 0, categoria_id: '' });

  const [isPayModalVisible, setIsPayModalVisible] = useState(false);
  const [gastoToPay, setGastoToPay] = useState<string | null>(null);
  const [selectedCuentaId, setSelectedCuentaId] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [gastosRes, catRes, cuentasRes] = await Promise.all([
        api.get('/expenses/record'),
        api.get('/expenses/categories'),
        api.get('/treasury/accounts')
      ]);
      setGastos(gastosRes.data);
      setCategorias(catRes.data);
      setCuentas(cuentasRes.data);
    } catch (error) {
      message.error('Error al cargar datos de gastos.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGasto = async () => {
    try {
      await api.post('/expenses/record', newGasto);
      message.success('Gasto registrado como pendiente de aprobación.');
      setIsModalVisible(false);
      setNewGasto({ concepto: '', monto: 0, categoria_id: '' });
      fetchData();
    } catch (error) {
      message.error('Error al registrar el gasto.');
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await api.put(`/expenses/${id}/approve`);
      message.success('Gasto aprobado.');
      fetchData();
    } catch (error) {
      message.error('Error al aprobar el gasto.');
    }
  };

  const handlePay = async () => {
    if (!selectedCuentaId) return message.warning('Selecciona una cuenta bancaria origen.');
    try {
      await api.put(`/expenses/${gastoToPay}/pay`, { cuenta_bancaria_id: selectedCuentaId });
      message.success('Gasto pagado, cuenta afectada y póliza generada.');
      setIsPayModalVisible(false);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al pagar el gasto.');
    }
  };

  const renderStatus = (status: string) => {
    const map: any = {
      pendiente: { color: 'warning', text: 'PENDIENTE DE APROBACIÓN', icon: <ClockCircleOutlined /> },
      aprobado: { color: 'processing', text: 'APROBADO', icon: <CheckCircleOutlined /> },
      pagado: { color: 'success', text: 'PAGADO', icon: <DollarOutlined /> },
      rechazado: { color: 'error', text: 'RECHAZADO', icon: null }
    };
    const s = map[status];
    if (!s) return <Tag>{status}</Tag>;
    return <Tag color={s.color} icon={s.icon}>{s.text}</Tag>;
  };

  const columnsMisGastos = [
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (val: string) => dayjs(val).format('DD/MM/YYYY') },
    { title: 'Concepto', dataIndex: 'concepto', key: 'concepto', render: (val: string) => <Text strong style={{ color: '#FFF' }}>{val}</Text> },
    { title: 'Categoría', dataIndex: 'categoria_nombre', key: 'categoria_nombre' },
    { title: 'Monto', dataIndex: 'monto', key: 'monto', render: (val: number) => <Text strong style={{ color: '#DAA520' }}>${val.toFixed(2)}</Text> },
    { title: 'Estado', dataIndex: 'estado', key: 'estado', render: (val: string) => renderStatus(val) },
  ];

  const columnsPorAprobar = [
    ...columnsMisGastos,
    { title: 'Solicitante', dataIndex: 'usuario_nombre', key: 'usuario_nombre' },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: GastoOperativo) => (
        <Space>
          {record.estado === 'pendiente' && (
            <Button size="small" type="primary" onClick={() => handleApprove(record.id)}>Aprobar</Button>
          )}
          {record.estado === 'aprobado' && (
            <Button 
              size="small" 
              style={{ backgroundColor: '#00A651', color: '#FFF', borderColor: '#00A651' }} 
              onClick={() => {
                setGastoToPay(record.id);
                setIsPayModalVisible(true);
              }}
            >
              Emitir Pago
            </Button>
          )}
        </Space>
      )
    }
  ];

  const totalPendiente = gastos.filter(g => g.estado === 'pendiente').reduce((sum, g) => sum + g.monto, 0);
  const totalPagado = gastos.filter(g => g.estado === 'pagado').reduce((sum, g) => sum + g.monto, 0);

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: '#DAA520', margin: 0 }}>
            <DollarOutlined /> Control de Gastos y Comprobaciones
          </Title>
        </Col>
        <Col>
          <Space>
            <Button icon={<SyncOutlined />} onClick={fetchData} loading={loading}>Actualizar</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
              Registrar Gasto (Viático)
            </Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} md={8}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic title={<Text style={{ color: '#B8B9BD' }}>Total Gastos Pagados (Mes)</Text>} value={totalPagado} precision={2} prefix="$" valueStyle={{ color: '#00A651' }} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic title={<Text style={{ color: '#B8B9BD' }}>Pendientes de Aprobación</Text>} value={totalPendiente} precision={2} prefix="$" valueStyle={{ color: '#F44336' }} />
          </Card>
        </Col>
      </Row>

      <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bodyStyle={{ padding: 0 }}>
        <Tabs defaultActiveKey="mis-gastos" style={{ padding: '0 24px' }}>
          <TabPane tab="Mis Gastos (Comprobaciones)" key="mis-gastos">
            <Table 
              dataSource={gastos} 
              columns={columnsMisGastos} 
              rowKey="id" 
              loading={loading} 
              className="dark-table"
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
          <TabPane tab="Administración (Aprobaciones)" key="admin">
            <Table 
              dataSource={gastos} 
              columns={columnsPorAprobar} 
              rowKey="id" 
              loading={loading} 
              className="dark-table"
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      <Modal
        title="Registrar Nuevo Gasto"
        open={isModalVisible}
        onOk={handleCreateGasto}
        onCancel={() => setIsModalVisible(false)}
        okText="Registrar"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            placeholder="Selecciona una Categoría"
            style={{ width: '100%' }}
            value={newGasto.categoria_id}
            onChange={(val) => setNewGasto({...newGasto, categoria_id: val})}
          >
            {categorias.map(c => <Select.Option key={c.id} value={c.id}>{c.nombre}</Select.Option>)}
          </Select>
          <Input 
            placeholder="Concepto (ej. Comida cliente, Taxi al aeropuerto)"
            value={newGasto.concepto}
            onChange={(e) => setNewGasto({...newGasto, concepto: e.target.value})}
          />
          <InputNumber
            placeholder="Monto"
            style={{ width: '100%' }}
            min={0}
            prefix="$"
            value={newGasto.monto}
            onChange={(val) => setNewGasto({...newGasto, monto: val || 0})}
          />
        </Space>
      </Modal>

      <Modal
        title="Emitir Pago a Gasto Aprobado"
        open={isPayModalVisible}
        onOk={handlePay}
        onCancel={() => setIsPayModalVisible(false)}
        okText="Pagar y Contabilizar"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Selecciona la cuenta bancaria de origen para emitir el pago:</Text>
          <Select
            placeholder="Cuenta Bancaria"
            style={{ width: '100%' }}
            value={selectedCuentaId}
            onChange={(val) => setSelectedCuentaId(val)}
          >
            {cuentas.map(c => (
              <Select.Option key={c.id} value={c.id}>
                {c.banco} ({c.numero_cuenta}) - Saldo: ${c.saldo_actual.toFixed(2)}
              </Select.Option>
            ))}
          </Select>
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
