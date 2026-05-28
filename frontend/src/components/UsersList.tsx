import React, { useEffect, useState } from 'react';
import { Button, Form as AntdForm, Input as AntdInput, Modal, Select as AntdSelect, Space, Table, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { api, getApiErrorMessage } from '../services/authService';

const { Option } = AntdSelect;

interface TenantUser {
  id: string;
  email: string;
  nombre_completo?: string;
  tipo_usuario: string;
  tenant_id?: string;
  is_active: boolean;
}

const UsersList: React.FC = () => {
  const [users, setUsers] = useState<TenantUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = AntdForm.useForm();

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/tenant-portal/usuarios');
      setUsers(response.data.usuarios);
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al cargar usuarios'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/tenant-portal/usuarios', values);
      message.success('Usuario creado correctamente');
      setModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error: any) {
      if (error?.errorFields) {
        return;
      }
      message.error(getApiErrorMessage(error, 'Error al crear usuario'));
    }
  };

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'nombre_completo',
      key: 'nombre_completo',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Tipo de Usuario',
      dataIndex: 'tipo_usuario',
      key: 'tipo_usuario',
      render: (tipo: string) => (
        <Tag color={tipo === 'admin_empresa' ? 'purple' : 'blue'}>
          {tipo === 'admin_empresa' ? 'Admin empresa' : 'Normal'}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, textAlign: 'left' }}>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ color: '#1B365D', margin: 0 }}>Usuarios del Tenant</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          Agregar Usuario
        </Button>
      </Space>

      <Table
        dataSource={users}
        columns={columns}
        loading={loading}
        rowKey="id"
      />

      <Modal
        title="Agregar Usuario"
        open={modalVisible}
        onOk={handleCreateUser}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        okText="Guardar"
        cancelText="Cancelar"
        destroyOnClose
      >
        <AntdForm layout="vertical" form={form} name="tenant_user_form">
          <AntdForm.Item
            name="nombre_completo"
            label="Nombre Completo"
            rules={[{ required: true, message: 'Ingresa el nombre completo' }]}
          >
            <AntdInput />
          </AntdForm.Item>

          <AntdForm.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Ingresa el email' },
              { type: 'email', message: 'Ingresa un email valido' }
            ]}
          >
            <AntdInput />
          </AntdForm.Item>

          <AntdForm.Item
            name="password"
            label="Contrasena temporal"
            rules={[{ required: true, message: 'Ingresa una contrasena temporal' }]}
          >
            <AntdInput.Password />
          </AntdForm.Item>

          <AntdForm.Item
            name="tipo_usuario"
            label="Tipo de Usuario"
            initialValue="normal"
            rules={[{ required: true, message: 'Selecciona el tipo de usuario' }]}
          >
            <AntdSelect placeholder="Seleccione el tipo de usuario">
              <Option value="normal">Normal</Option>
              <Option value="admin_empresa">Admin empresa</Option>
            </AntdSelect>
          </AntdForm.Item>
        </AntdForm>
      </Modal>
    </div>
  );
};

export default UsersList;
