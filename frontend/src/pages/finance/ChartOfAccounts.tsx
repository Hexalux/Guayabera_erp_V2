import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Switch, message, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { financeService, CuentaContable } from '../../services/financeService';

const { Title } = Typography;
const { Option } = Select;

const ChartOfAccounts: React.FC = () => {
  const [cuentas, setCuentas] = useState<CuentaContable[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchCuentas = async () => {
    setLoading(true);
    try {
      const data = await financeService.getCuentas();
      setCuentas(data);
    } catch (error) {
      message.error('Error al cargar el plan de cuentas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCuentas();
  }, []);

  const handleOpenModal = () => {
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  const handleCreate = async (values: CuentaContable) => {
    try {
      await financeService.createCuenta(values);
      message.success('Cuenta creada exitosamente');
      setIsModalVisible(false);
      fetchCuentas();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al crear la cuenta');
    }
  };

  const columns = [
    {
      title: 'Código',
      dataIndex: 'codigo',
      key: 'codigo',
      render: (text: string, record: CuentaContable) => (
        <span style={{ fontWeight: record.es_agrupadora ? 'bold' : 'normal' }}>{text}</span>
      ),
    },
    {
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
      render: (text: string, record: CuentaContable) => (
        <span style={{ fontWeight: record.es_agrupadora ? 'bold' : 'normal', paddingLeft: `${(record.nivel - 1) * 20}px` }}>
          {text}
        </span>
      ),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
    },
    {
      title: 'Naturaleza',
      dataIndex: 'naturaleza',
      key: 'naturaleza',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: CuentaContable) => (
        <Space size="middle">
          <Button type="text" icon={<EditOutlined />} />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3}>Catálogo de Cuentas</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenModal}>
          Nueva Cuenta
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={cuentas}
        rowKey="id"
        loading={loading}
        pagination={false}
      />

      <Modal
        title="Crear Nueva Cuenta Contable"
        open={isModalVisible}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        okText="Guardar"
        cancelText="Cancelar"
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="codigo"
            label="Código de Cuenta"
            rules={[{ required: true, message: 'Ingrese el código' }]}
          >
            <Input placeholder="Ej. 101.01.001" />
          </Form.Item>

          <Form.Item
            name="nombre"
            label="Nombre de Cuenta"
            rules={[{ required: true, message: 'Ingrese el nombre' }]}
          >
            <Input placeholder="Ej. Bancos Nacionales" />
          </Form.Item>

          <Form.Item
            name="tipo"
            label="Tipo de Cuenta"
            rules={[{ required: true, message: 'Seleccione el tipo' }]}
          >
            <Select placeholder="Seleccione">
              <Option value="activo">Activo</Option>
              <Option value="pasivo">Pasivo</Option>
              <Option value="capital">Capital</Option>
              <Option value="ingresos">Ingresos</Option>
              <Option value="costos">Costos</Option>
              <Option value="gastos">Gastos</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="naturaleza"
            label="Naturaleza"
            rules={[{ required: true, message: 'Seleccione la naturaleza' }]}
          >
            <Select placeholder="Seleccione">
              <Option value="deudora">Deudora</Option>
              <Option value="acreedora">Acreedora</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="nivel"
            label="Nivel (1 a 5)"
            initialValue={1}
            rules={[{ required: true }]}
          >
            <Select>
              {[1, 2, 3, 4, 5].map(n => <Option key={n} value={n}>{n}</Option>)}
            </Select>
          </Form.Item>

          <Form.Item name="es_agrupadora" valuePropName="checked" initialValue={false}>
            <Switch checkedChildren="Agrupadora" unCheckedChildren="Afectable" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ChartOfAccounts;
