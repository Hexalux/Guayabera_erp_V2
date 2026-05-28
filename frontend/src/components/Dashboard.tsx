import React, { useEffect, useState } from 'react';
import { Button, Card, Col, Empty, Form, Input, Modal, Row, Select, Statistic, Table, Tag, message } from 'antd';
import { BankOutlined, CalendarOutlined, FileProtectOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { api, getApiErrorMessage } from '../services/authService';

interface TenantLicense {
  id: string;
  codigo: string;
  tipo_licencia_nombre?: string;
  fecha_inicio: string;
  fecha_fin: string;
  activa: boolean;
  notas?: string;
}

interface TenantUser {
  id: string;
  email: string;
  nombre_completo?: string;
  tipo_usuario: string;
  is_active: boolean;
}

interface TenantCompany {
  id: string;
  name: string;
  subdomain: string;
  contact_email?: string;
  is_active: boolean;
}

interface TenantModule {
  key: string;
  nombre: string;
  habilitado: boolean;
}

interface LicenseType {
  id: string;
  nombre: string;
  duracion_dias: number;
  precio?: number;
}

interface TenantSummary {
  tenant: {
    id: string;
    name: string;
    subdomain: string;
    contact_email?: string;
    is_active: boolean;
    es_grupo_corporativo: boolean;
  };
  licencia_activa?: TenantLicense | null;
  licencias: TenantLicense[];
  usuarios: TenantUser[];
  empresas: TenantCompany[];
  modulos: TenantModule[];
}

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<TenantSummary | null>(null);
  const [licenseTypes, setLicenseTypes] = useState<LicenseType[]>([]);
  const [loading, setLoading] = useState(false);
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [requestForm] = Form.useForm();

  const fetchTenantData = async () => {
    setLoading(true);
    try {
      const [summaryRes, licenseTypesRes] = await Promise.all([
        api.get('/tenant-portal/resumen'),
        api.get('/tenant-portal/tipos-licencia'),
      ]);

      setSummary(summaryRes.data);
      setLicenseTypes(licenseTypesRes.data.tipos_licencia);
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al cargar el dashboard del tenant'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenantData();
  }, []);

  const handleRequestLicense = async (values: any) => {
    try {
      await api.post('/tenant-portal/solicitar-licencia', values);
      message.success('Solicitud de licencia enviada al super-admin');
      setRequestModalOpen(false);
      requestForm.resetFields();
      fetchTenantData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al solicitar licencia'));
    }
  };

  const activeLicense = summary?.licencia_activa;

  const userColumns = [
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
      title: 'Rol',
      dataIndex: 'tipo_usuario',
      key: 'tipo_usuario',
      render: (role: string) => <Tag>{role}</Tag>,
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => <Tag color={isActive ? 'success' : 'error'}>{isActive ? 'Activo' : 'Inactivo'}</Tag>,
    },
  ];

  const companyColumns = [
    {
      title: 'Empresa',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Subdominio',
      dataIndex: 'subdomain',
      key: 'subdomain',
    },
    {
      title: 'Contacto',
      dataIndex: 'contact_email',
      key: 'contact_email',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => <Tag color={isActive ? 'success' : 'error'}>{isActive ? 'Activa' : 'Inactiva'}</Tag>,
    },
  ];

  const licenseColumns = [
    {
      title: 'Codigo',
      dataIndex: 'codigo',
      key: 'codigo',
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_licencia_nombre',
      key: 'tipo_licencia_nombre',
    },
    {
      title: 'Inicio',
      dataIndex: 'fecha_inicio',
      key: 'fecha_inicio',
      render: (value: string) => dayjs(value).format('YYYY-MM-DD'),
    },
    {
      title: 'Vence',
      dataIndex: 'fecha_fin',
      key: 'fecha_fin',
      render: (value: string) => dayjs(value).format('YYYY-MM-DD'),
    },
    {
      title: 'Estado',
      dataIndex: 'activa',
      key: 'activa',
      render: (isActive: boolean) => <Tag color={isActive ? 'success' : 'warning'}>{isActive ? 'Activa' : 'Pendiente'}</Tag>,
    },
  ];

  return (
    <div style={{ padding: 24, textAlign: 'left' }}>
      <Row align="middle" justify="space-between" style={{ marginBottom: 24 }}>
        <Col>
          <h1 style={{ color: '#1B365D', marginBottom: 4 }}>Dashboard de Tenant</h1>
          <div style={{ color: '#5B6472' }}>{summary?.tenant?.name || 'Empresa'}</div>
        </Col>
        <Col>
          <Button type="primary" onClick={() => setRequestModalOpen(true)}>
            Solicitar licencia
          </Button>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="Licencia activa" value={activeLicense ? 'Si' : 'No'} prefix={<FileProtectOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="Usuarios" value={summary?.usuarios.length || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="Empresas" value={summary?.empresas.length || 0} prefix={<BankOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card loading={loading}>
            <Statistic title="Modulos activos" value={summary?.modulos.filter((module) => module.habilitado).length || 0} prefix={<TeamOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={10}>
          <Card title="Licencia activa" loading={loading}>
            {activeLicense ? (
              <div>
                <p><strong>Tipo:</strong> {activeLicense.tipo_licencia_nombre || activeLicense.codigo}</p>
                <p><CalendarOutlined /> Activa desde {dayjs(activeLicense.fecha_inicio).format('YYYY-MM-DD')}</p>
                <p><CalendarOutlined /> Vence el {dayjs(activeLicense.fecha_fin).format('YYYY-MM-DD')}</p>
                <Tag color="success">Activa</Tag>
              </div>
            ) : (
              <Empty description="Sin licencia activa" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="Modulos disponibles" loading={loading}>
            <SpaceWrap>
              {summary?.modulos.map((module) => (
                <Tag key={module.key} color={module.habilitado ? 'blue' : 'default'}>
                  {module.nombre}
                </Tag>
              ))}
            </SpaceWrap>
          </Card>
        </Col>
      </Row>

      <Card title="Historial de licencias" style={{ marginTop: 16 }} loading={loading}>
        <Table dataSource={summary?.licencias || []} columns={licenseColumns} rowKey="id" pagination={{ pageSize: 5 }} />
      </Card>

      <Card title="Usuarios configurados" style={{ marginTop: 16 }} loading={loading}>
        <Table dataSource={summary?.usuarios || []} columns={userColumns} rowKey="id" pagination={{ pageSize: 5 }} />
      </Card>

      <Card title="Empresas configuradas" style={{ marginTop: 16 }} loading={loading}>
        <Table dataSource={summary?.empresas || []} columns={companyColumns} rowKey="id" pagination={{ pageSize: 5 }} />
      </Card>

      <Modal
        title="Solicitar nueva licencia"
        open={requestModalOpen}
        onCancel={() => {
          setRequestModalOpen(false);
          requestForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <Form form={requestForm} layout="vertical" onFinish={handleRequestLicense}>
          <Form.Item
            name="tipo_licencia_id"
            label="Tipo de licencia"
            rules={[{ required: true, message: 'Selecciona el tipo de licencia' }]}
          >
            <Select placeholder="Selecciona tipo de licencia">
              {licenseTypes.map((type) => (
                <Select.Option key={type.id} value={type.id}>
                  {type.nombre} ({type.duracion_dias} dias)
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="notas" label="Notas">
            <Input.TextArea placeholder="Describe la necesidad o cantidad de usuarios esperada..." />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Enviar solicitud
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

const SpaceWrap: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>{children}</div>
);

export default Dashboard;
