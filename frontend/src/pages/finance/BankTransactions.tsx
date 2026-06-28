import React, { useState, useEffect } from 'react';
import { Card, Typography, Table, Tag, Button, Space, message, Select } from 'antd';
import { UnorderedListOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface TransaccionBancaria {
  id: string;
  cuenta_id: string;
  fecha: string;
  tipo: string;
  monto: number;
  referencia: string;
  concepto: string;
  metodo_pago: string;
  estado_cheque?: string;
  poliza_id?: string;
}

export const BankTransactions: React.FC = () => {
  const [transacciones, setTransacciones] = useState<TransaccionBancaria[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await api.get('/treasury/transactions');
      setTransacciones(res.data);
    } catch (error) {
      message.error('Error al cargar historial bancario');
    } finally {
      setLoading(false);
    }
  };

  const handleChangeChequeStatus = async (id: string, newStatus: string) => {
    try {
      await api.put(`/treasury/transactions/${id}/estado`, { estado: newStatus });
      message.success(`Cheque marcado como ${newStatus}`);
      fetchTransactions();
    } catch (error) {
      message.error('Error al actualizar cheque');
    }
  };

  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      render: (val: string) => <Text style={{ color: '#FFF' }}>{dayjs(val).format('DD/MM/YYYY HH:mm')}</Text>
    },
    {
      title: 'Concepto / Ref',
      key: 'concepto',
      render: (_: any, record: TransaccionBancaria) => (
        <Space direction="vertical" size="small">
          <Text strong style={{ color: '#2196F3' }}>{record.concepto}</Text>
          <Text style={{ color: '#B8B9BD', fontSize: '12px' }}>{record.referencia || 'N/A'}</Text>
        </Space>
      )
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      render: (val: string) => (
        <Tag color={val === 'ingreso' ? 'success' : 'error'}>{val.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Método / Cheque',
      key: 'metodo',
      render: (_: any, record: TransaccionBancaria) => (
        <Space direction="vertical" size="small">
          <Tag color="geekblue">{record.metodo_pago.toUpperCase()}</Tag>
          {record.metodo_pago === 'cheque' && (
            <Select 
              size="small" 
              value={record.estado_cheque || 'emitido'} 
              style={{ width: 120 }}
              onChange={(val) => handleChangeChequeStatus(record.id, val)}
              options={[
                { value: 'emitido', label: 'Emitido' },
                { value: 'cobrado', label: 'Cobrado' },
                { value: 'rebotado', label: 'Rebotado / Devuelto' },
                { value: 'cancelado', label: 'Cancelado' }
              ]}
            />
          )}
        </Space>
      )
    },
    {
      title: 'Monto',
      dataIndex: 'monto',
      key: 'monto',
      render: (val: number, record: TransaccionBancaria) => (
        <Text strong style={{ color: record.tipo === 'ingreso' ? '#00A651' : '#F44336' }}>
          {record.tipo === 'ingreso' ? '+' : '-'}${val.toFixed(2)}
        </Text>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title level={2} style={{ color: '#DAA520', margin: 0 }}>
            <UnorderedListOutlined /> Operaciones Bancarias
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Libro mayor de bancos y control de cheques</Text>
        </div>
        <Button icon={<SyncOutlined />} onClick={fetchTransactions} loading={loading}>
          Actualizar
        </Button>
      </div>

      <Card 
        style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          dataSource={transacciones} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
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
      `}</style>
    </div>
  );
};
