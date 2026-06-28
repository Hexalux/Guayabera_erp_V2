import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Table, Typography, Space, Tag, Modal, Input, InputNumber, Select, message, Statistic } from 'antd';
import { BankOutlined, WalletOutlined, ArrowUpOutlined, ArrowDownOutlined, SyncOutlined, PlusOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;
const { Option } = Select;

interface CuentaBancaria {
  id: string;
  banco: string;
  numero_cuenta: string;
  clabe: string;
  saldo_actual: number;
  moneda: string;
  activa: boolean;
}

export const TreasuryDashboard: React.FC = () => {
  const [cuentas, setCuentas] = useState<CuentaBancaria[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modals state
  const [isNewAccountModalVisible, setIsNewAccountModalVisible] = useState(false);
  const [isTransactionModalVisible, setIsTransactionModalVisible] = useState(false);
  const [transactionType, setTransactionType] = useState<'ingreso' | 'egreso'>('ingreso');
  
  // Forms state
  const [newAccount, setNewAccount] = useState({ banco: '', numero_cuenta: '', clabe: '' });
  const [transaction, setTransaction] = useState({ cuenta_id: '', monto: 0, concepto: '', referencia: '', metodo_pago: 'transferencia' });

  useEffect(() => {
    fetchCuentas();
  }, []);

  const fetchCuentas = async () => {
    setLoading(true);
    try {
      const res = await api.get('/treasury/accounts');
      setCuentas(res.data);
    } catch (error) {
      console.error('Error fetching accounts', error);
      message.error('No se pudieron cargar las cuentas bancarias.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    try {
      await api.post('/treasury/accounts', newAccount);
      message.success('Cuenta bancaria creada exitosamente');
      setIsNewAccountModalVisible(false);
      fetchCuentas();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al crear la cuenta');
    }
  };

  const handleCreateTransaction = async () => {
    try {
      if (transactionType === 'ingreso') {
        await api.post('/treasury/transactions/ingreso', transaction);
        message.success('Depósito registrado y contabilizado.');
      } else {
        await api.post('/treasury/transactions/egreso', transaction);
        message.success('Egreso registrado y contabilizado.');
      }
      setIsTransactionModalVisible(false);
      fetchCuentas();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error en la transacción');
    }
  };

  const totalSaldo = cuentas.reduce((sum, c) => sum + c.saldo_actual, 0);

  const columns = [
    { 
      title: 'Banco', 
      dataIndex: 'banco', 
      key: 'banco',
      render: (text: string) => <Text strong style={{ color: '#00A651' }}>{text}</Text>
    },
    { 
      title: 'Cuenta / CLABE', 
      key: 'cuenta',
      render: (_: any, record: CuentaBancaria) => (
        <Space direction="vertical" size="small">
          <Text style={{ color: '#FFF' }}>{record.numero_cuenta}</Text>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>{record.clabe}</Text>
        </Space>
      )
    },
    { 
      title: 'Moneda', 
      dataIndex: 'moneda', 
      key: 'moneda',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    { 
      title: 'Saldo Actual', 
      dataIndex: 'saldo_actual', 
      key: 'saldo_actual',
      render: (val: number) => <Text strong style={{ color: '#DAA520', fontSize: '16px' }}>${val.toFixed(2)}</Text>
    },
    {
      title: 'Acciones Rápidas',
      key: 'acciones',
      render: (_: any, record: CuentaBancaria) => (
        <Space>
          <Button 
            size="small" 
            style={{ backgroundColor: '#0C0E14', color: '#00A651', borderColor: '#00A651' }}
            icon={<ArrowUpOutlined />}
            onClick={() => {
              setTransactionType('ingreso');
              setTransaction({ ...transaction, cuenta_id: record.id, monto: 0, concepto: '', metodo_pago: 'transferencia' });
              setIsTransactionModalVisible(true);
            }}
          >
            Depositar
          </Button>
          <Button 
            size="small" 
            style={{ backgroundColor: '#0C0E14', color: '#F44336', borderColor: '#F44336' }}
            icon={<ArrowDownOutlined />}
            onClick={() => {
              setTransactionType('egreso');
              setTransaction({ ...transaction, cuenta_id: record.id, monto: 0, concepto: '', metodo_pago: 'transferencia' });
              setIsTransactionModalVisible(true);
            }}
          >
            Retirar
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: '#DAA520', margin: 0 }}>
            <BankOutlined /> Control de Tesorería
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Cuentas Bancarias y Flujo de Efectivo</Text>
        </Col>
        <Col>
          <Space>
            <Button icon={<SyncOutlined />} onClick={fetchCuentas} loading={loading}>
              Actualizar
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
              onClick={() => setIsNewAccountModalVisible(true)}
            >
              Nueva Cuenta Bancaria
            </Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} md={8}>
          <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
            <Statistic 
              title={<Text style={{ color: '#B8B9BD' }}>Saldo Consolidado Total</Text>}
              value={totalSaldo} 
              precision={2} 
              prefix="$" 
              valueStyle={{ color: '#DAA520', fontWeight: 'bold' }} 
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={<Text style={{ color: '#FFF' }}><WalletOutlined /> Cuentas Registradas</Text>}
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={cuentas} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={false}
          className="dark-table"
        />
      </Card>

      {/* Modal Nueva Cuenta */}
      <Modal
        title="Registrar Cuenta Bancaria"
        open={isNewAccountModalVisible}
        onOk={handleCreateAccount}
        onCancel={() => setIsNewAccountModalVisible(false)}
        okText="Registrar"
        cancelText="Cancelar"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input 
            placeholder="Nombre del Banco (ej. Banorte, Caja Chica)" 
            value={newAccount.banco}
            onChange={e => setNewAccount({...newAccount, banco: e.target.value})}
          />
          <Input 
            placeholder="Número de Cuenta" 
            value={newAccount.numero_cuenta}
            onChange={e => setNewAccount({...newAccount, numero_cuenta: e.target.value})}
          />
          <Input 
            placeholder="CLABE Interbancaria" 
            value={newAccount.clabe}
            onChange={e => setNewAccount({...newAccount, clabe: e.target.value})}
          />
        </Space>
      </Modal>

      {/* Modal Transacción */}
      <Modal
        title={transactionType === 'ingreso' ? "Registrar Depósito" : "Registrar Retiro/Cheque"}
        open={isTransactionModalVisible}
        onOk={handleCreateTransaction}
        onCancel={() => setIsTransactionModalVisible(false)}
        okText="Procesar y Contabilizar"
        cancelText="Cancelar"
        okButtonProps={{ danger: transactionType === 'egreso', style: { backgroundColor: transactionType === 'ingreso' ? '#00A651' : undefined } }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            style={{ width: '100%' }}
            value={transaction.metodo_pago}
            onChange={(val) => setTransaction({ ...transaction, metodo_pago: val })}
            options={[
              { value: 'transferencia', label: 'Transferencia Bancaria' },
              { value: 'efectivo', label: 'Efectivo / Depósito en Ventanilla' },
              { value: 'cheque', label: 'Cheque' },
              { value: 'tarjeta', label: 'Tarjeta de Crédito / Débito' },
            ]}
          />
          <InputNumber 
            style={{ width: '100%' }}
            placeholder="Monto" 
            prefix="$"
            min={0}
            value={transaction.monto}
            onChange={val => setTransaction({...transaction, monto: val || 0})}
          />
          <Input 
            placeholder="Concepto de la transacción" 
            value={transaction.concepto}
            onChange={e => setTransaction({...transaction, concepto: e.target.value})}
          />
          <Input 
            placeholder={transaction.metodo_pago === 'cheque' ? "Número de Cheque" : "Referencia (Folio Transferencia)"} 
            value={transaction.referencia}
            onChange={e => setTransaction({...transaction, referencia: e.target.value})}
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
