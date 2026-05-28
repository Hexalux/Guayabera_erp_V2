import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Form as AntdForm, 
  Input, 
  Modal, 
  Tabs, 
  message, 
  Select,
  Space, 
  Popconfirm,
  Tag,
  Typography,
  Switch
} from 'antd';
import { CheckCircleOutlined, DeleteOutlined, EditOutlined, MailOutlined, PlusOutlined, StopOutlined } from '@ant-design/icons';
import { api, getApiErrorMessage } from '../services/authService';

const { TabPane } = Tabs;
const { Title } = Typography;

interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  contact_email: string;
  contact_phone?: string;
  descripcion: string;
  is_active: boolean;
  grupo_corporativo_id?: string;
  created_at: string;
}

interface Corporation {
  id: string;
  name: string;
  descripcion: string;
  is_active: boolean;
  empresas_count?: number;
  created_at: string;
}

interface License {
  id: string;
  tipo_licencia_id: string;
  tipo_licencia_nombre?: string;
  codigo: string;
  fecha_inicio: string;
  fecha_fin: string;
  activa: boolean;
  tenant_id?: string;
  created_at: string;
}

interface LicenseType {
  id: string;
  nombre: string;
  descripcion?: string;
  duracion_dias: number;
  precio?: number;
  es_prueba: boolean;
}

interface SuperAdminUser {
  id: string;
  email: string;
  nombre_completo?: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

const SuperAdminDashboard: React.FC = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [licenses, setLicenses] = useState<License[]>([]);
  const [licenseTypes, setLicenseTypes] = useState<LicenseType[]>([]);
  const [superAdmins, setSuperAdmins] = useState<SuperAdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Forms
  const [tenantForm] = AntdForm.useForm();
  const [corporationForm] = AntdForm.useForm();
  const [licenseForm] = AntdForm.useForm();
  const [superAdminForm] = AntdForm.useForm();
  
  // Modals
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [showCorporationModal, setShowCorporationModal] = useState(false);
  const [showLicenseModal, setShowLicenseModal] = useState(false);
  const [showSuperAdminModal, setShowSuperAdminModal] = useState(false);
  const [showAssignCorporationModal, setShowAssignCorporationModal] = useState(false);
  const [showCorporationTenantsModal, setShowCorporationTenantsModal] = useState(false);
  const [showManageCorporationTenantsModal, setShowManageCorporationTenantsModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm] = AntdForm.useForm();
  const [assignCorporationForm] = AntdForm.useForm();
  const [manageCorporationTenantsForm] = AntdForm.useForm();
  const [selectedTenant, setSelectedTenant] = useState<string | null>(null);
  const [selectedCorporation, setSelectedCorporation] = useState<Corporation | null>(null);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [editingCorporation, setEditingCorporation] = useState<Corporation | null>(null);
  const [editingSuperAdmin, setEditingSuperAdmin] = useState<SuperAdminUser | null>(null);

  // Load data on mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tenantsRes, corporationsRes, licensesRes, licenseTypesRes, superAdminsRes] = await Promise.all([
        api.get('/admin/tenants'),
        api.get('/admin/corporaciones'),
        api.get('/admin/licencias'),
        api.get('/licencias/tipos-licencia'),
        api.get('/admin/super-admins')
      ]);

      setTenants(tenantsRes.data.tenants);
      setCorporations(corporationsRes.data.corporaciones);
      setLicenses(licensesRes.data.licencias);
      setLicenseTypes(licenseTypesRes.data);
      setSuperAdmins(superAdminsRes.data.super_admins);
    } catch (error) {
      message.error('Error al cargar los datos');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Tenant operations
  const openCreateTenantModal = () => {
    setEditingTenant(null);
    tenantForm.resetFields();
    setShowTenantModal(true);
  };

  const openEditTenantModal = (tenant: Tenant) => {
    setEditingTenant(tenant);
    tenantForm.setFieldsValue({
      name: tenant.name,
      subdomain: tenant.subdomain,
      contact_email: tenant.contact_email,
      contact_phone: tenant.contact_phone,
      grupo_corporativo_id: tenant.grupo_corporativo_id,
      descripcion: tenant.descripcion,
      is_active: tenant.is_active,
    });
    setShowTenantModal(true);
  };

  const handleSaveTenant = async (values: any) => {
    try {
      const payload = {
        name: values.name,
        subdomain: values.subdomain,
        contact_email: values.contact_email,
        contact_phone: values.contact_phone,
        grupo_corporativo_id: values.grupo_corporativo_id,
        descripcion: values.descripcion,
        is_active: values.is_active,
      };

      if (editingTenant) {
        await api.put(`/admin/tenants/${editingTenant.id}`, payload);
      } else {
        await api.post('/admin/crear-tenant', payload);
      }

      message.success(`Tenant ${editingTenant ? 'actualizado' : 'creado'} exitosamente`);
      setShowTenantModal(false);
      setEditingTenant(null);
      tenantForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${editingTenant ? 'actualizar' : 'crear'} el tenant`));
    }
  };

  const handleActivateDeactivateTenant = async (id: string, activate: boolean) => {
    try {
      const url = activate 
        ? `/admin/activar-tenant/${id}`
        : `/admin/desactivar-tenant/${id}`;
        
      await api.put(url);

      message.success(`Tenant ${activate ? 'activado' : 'desactivado'} exitosamente`);
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${activate ? 'activar' : 'desactivar'} el tenant`));
    }
  };

  // Corporation operations
  const handleCreateCorporation = async (values: any) => {
    try {
      await api.post('/admin/crear-corporacion', {
        nombre: values.name,
        descripcion: values.descripcion
      });

      message.success('Corporación creada exitosamente');
      setShowCorporationModal(false);
      corporationForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al crear la corporación'));
    }
  };

  const openCreateCorporationModal = () => {
    setEditingCorporation(null);
    corporationForm.resetFields();
    setShowCorporationModal(true);
  };

  const openEditCorporationModal = (corporation: Corporation) => {
    setEditingCorporation(corporation);
    corporationForm.setFieldsValue({
      name: corporation.name,
      descripcion: corporation.descripcion,
      is_active: corporation.is_active,
    });
    setShowCorporationModal(true);
  };

  const handleSaveCorporation = async (values: any) => {
    try {
      const payload = {
        nombre: values.name,
        descripcion: values.descripcion,
        is_active: values.is_active,
      };

      if (editingCorporation) {
        await api.put(`/admin/corporaciones/${editingCorporation.id}`, payload);
      } else {
        await api.post('/admin/crear-corporacion', payload);
      }

      message.success(`Corporacion ${editingCorporation ? 'actualizada' : 'creada'} exitosamente`);
      setShowCorporationModal(false);
      setEditingCorporation(null);
      corporationForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${editingCorporation ? 'actualizar' : 'crear'} la corporacion`));
    }
  };

  const handleActivateDeactivateCorporation = async (id: string, activate: boolean) => {
    try {
      const url = activate
        ? `/admin/corporaciones/${id}/activar`
        : `/admin/corporaciones/${id}/desactivar`;

      await api.put(url);

      message.success(`Corporacion ${activate ? 'activada' : 'desactivada'} exitosamente`);
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${activate ? 'activar' : 'desactivar'} la corporacion`));
    }
  };

  // Invite admin operations
  const handleInviteAdmin = async (values: any) => {
    if (!selectedTenant) return;

    try {
      await api.post('/admin/invitar-tenant-admin', {
        email: values.email,
        tenant_id: selectedTenant
      });

      message.success('Invitación enviada exitosamente');
      setShowInviteModal(false);
      inviteForm.resetFields();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al enviar la invitación'));
    }
  };

  const handleCreateLicense = async (values: any) => {
    try {
      await api.post('/licencias/licencias', {
        tenant_id: values.tenant_id,
        tipo_licencia_id: values.tipo_licencia_id,
        notas: values.notas
      });

      message.success('Licencia creada exitosamente');
      setShowLicenseModal(false);
      licenseForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al crear la licencia'));
    }
  };

  const handleCreateSuperAdmin = async (values: any) => {
    try {
      await api.post('/admin/super-admins', values);

      message.success('Super admin creado exitosamente');
      setShowSuperAdminModal(false);
      superAdminForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al crear el super admin'));
    }
  };

  const openCreateSuperAdminModal = () => {
    setEditingSuperAdmin(null);
    superAdminForm.resetFields();
    setShowSuperAdminModal(true);
  };

  const openEditSuperAdminModal = (admin: SuperAdminUser) => {
    setEditingSuperAdmin(admin);
    superAdminForm.setFieldsValue({
      nombre_completo: admin.nombre_completo,
      email: admin.email,
      is_verified: admin.is_verified,
      is_active: admin.is_active,
    });
    setShowSuperAdminModal(true);
  };

  const handleSaveSuperAdmin = async (values: any) => {
    try {
      const payload = {
        email: values.email,
        nombre_completo: values.nombre_completo,
        password: values.password,
        is_verified: values.is_verified,
        is_active: values.is_active,
      };

      if (editingSuperAdmin) {
        await api.put(`/admin/super-admins/${editingSuperAdmin.id}`, payload);
      } else {
        await api.post('/admin/super-admins', payload);
      }

      message.success(`Super admin ${editingSuperAdmin ? 'actualizado' : 'creado'} exitosamente`);
      setShowSuperAdminModal(false);
      setEditingSuperAdmin(null);
      superAdminForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${editingSuperAdmin ? 'actualizar' : 'crear'} el super admin`));
    }
  };

  const handleActivateDeactivateSuperAdmin = async (id: string, activate: boolean) => {
    try {
      const url = activate
        ? `/admin/super-admins/${id}/activar`
        : `/admin/super-admins/${id}/desactivar`;

      await api.put(url);

      message.success(`Super admin ${activate ? 'activado' : 'desactivado'} exitosamente`);
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, `Error al ${activate ? 'activar' : 'desactivar'} el super admin`));
    }
  };

  const handleAssignCorporation = async (values: any) => {
    if (!selectedTenant) return;

    try {
      await api.post('/admin/asignar-tenant-a-corporacion', {
        tenant_id: selectedTenant,
        corporation_id: values.corporation_id
      });

      message.success('Tenant asignado a corporacion exitosamente');
      setShowAssignCorporationModal(false);
      setSelectedTenant(null);
      assignCorporationForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al asignar corporacion'));
    }
  };

  const getCorporationName = (corporationId?: string) => {
    if (!corporationId) return 'Independiente';
    return corporations.find((corporation) => corporation.id === corporationId)?.name || 'Sin relacion';
  };

  const getCorporationTenants = (corporationId?: string) => (
    tenants.filter((tenant) => tenant.grupo_corporativo_id === corporationId)
  );

  const openManageCorporationTenants = (corporation: Corporation) => {
    setSelectedCorporation(corporation);
    manageCorporationTenantsForm.setFieldsValue({
      tenant_ids: getCorporationTenants(corporation.id).map((tenant) => tenant.id)
    });
    setShowManageCorporationTenantsModal(true);
  };

  const handleManageCorporationTenants = async (values: any) => {
    if (!selectedCorporation) return;

    try {
      await api.put(`/admin/corporaciones/${selectedCorporation.id}/tenants`, {
        tenant_ids: values.tenant_ids || []
      });

      message.success('Empresas de la corporacion actualizadas');
      setShowManageCorporationTenantsModal(false);
      setSelectedCorporation(null);
      manageCorporationTenantsForm.resetFields();
      fetchData();
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al actualizar empresas de la corporacion'));
    }
  };

  // Columns for tables
  const tenantColumns = [
    {
      title: 'Nombre',
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
      title: 'Corporacion',
      dataIndex: 'grupo_corporativo_id',
      key: 'grupo_corporativo_id',
      render: (corporationId?: string) => (
        <Tag color={corporationId ? 'blue' : 'default'}>
          {getCorporationName(corporationId)}
        </Tag>
      ),
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
    {
      title: 'Estado',
      key: 'is_active',
      render: (text: any, record: Tenant) => (
        <Tag color={record.is_active ? 'success' : 'error'}>
          {record.is_active ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (text: any, record: Tenant) => (
        <Space size="middle">
          <Button
            icon={<EditOutlined />}
            onClick={() => openEditTenantModal(record)}
          >
            Editar
          </Button>
          <Button 
            icon={<MailOutlined />} 
            onClick={() => {
              setSelectedTenant(record.id);
              setShowInviteModal(true);
            }}
          >
            Invitar Admin
          </Button>
          <Button
            onClick={() => {
              setSelectedTenant(record.id);
              assignCorporationForm.setFieldsValue({
                corporation_id: record.grupo_corporativo_id
              });
              setShowAssignCorporationModal(true);
            }}
          >
            Asignar corporacion
          </Button>
          <Popconfirm
            title={record.is_active ? "¿Desactivar este tenant?" : "¿Activar este tenant?"}
            onConfirm={() => handleActivateDeactivateTenant(record.id, !record.is_active)}
            okText="Sí"
            cancelText="No"
          >
            <Button icon={record.is_active ? <StopOutlined /> : <CheckCircleOutlined />}>
              {record.is_active ? 'Desactivar' : 'Activar'}
            </Button>
          </Popconfirm>
          <Button danger disabled icon={<DeleteOutlined />}>
            Borrar
          </Button>
        </Space>
      ),
    },
  ];

  const corporationColumns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
    {
      title: 'Empresas',
      key: 'empresas_count',
      render: (record: Corporation) => getCorporationTenants(record.id).length,
    },
    {
      title: 'Estado',
      key: 'is_active',
      render: (record: Corporation) => (
        <Tag color={record.is_active ? 'success' : 'error'}>
          {record.is_active ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Fecha de Creación',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (record: Corporation) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => openEditCorporationModal(record)}
          >
            Editar
          </Button>
          <Button
            onClick={() => {
              setSelectedCorporation(record);
              setShowCorporationTenantsModal(true);
            }}
          >
            Ver empresas
          </Button>
          <Button onClick={() => openManageCorporationTenants(record)}>
            Asignar empresas
          </Button>
          <Popconfirm
            title={record.is_active ? "¿Desactivar esta corporacion?" : "¿Activar esta corporacion?"}
            onConfirm={() => handleActivateDeactivateCorporation(record.id, !record.is_active)}
            okText="Si"
            cancelText="No"
          >
            <Button icon={record.is_active ? <StopOutlined /> : <CheckCircleOutlined />}>
              {record.is_active ? 'Desactivar' : 'Activar'}
            </Button>
          </Popconfirm>
          <Button danger disabled icon={<DeleteOutlined />}>
            Borrar
          </Button>
        </Space>
      ),
    },
  ];

  const licenseColumns = [
    {
      title: 'Código',
      dataIndex: 'codigo',
      key: 'codigo',
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant_id',
      key: 'tenant_id',
      render: (tenantId: string) => tenants.find((tenant) => tenant.id === tenantId)?.name || tenantId,
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_licencia_id',
      key: 'tipo_licencia_id',
      render: (tipoId: string) => licenseTypes.find((tipo) => tipo.id === tipoId)?.nombre || tipoId,
    },
    {
      title: 'Fecha Inicio',
      dataIndex: 'fecha_inicio',
      key: 'fecha_inicio',
    },
    {
      title: 'Fecha Fin',
      dataIndex: 'fecha_fin',
      key: 'fecha_fin',
    },
    {
      title: 'Activa',
      key: 'activa',
      render: (text: any, record: License) => (
        <Tag color={record.activa ? 'success' : 'error'}>
          {record.activa ? 'Sí' : 'No'}
        </Tag>
      ),
    },
  ];

  const superAdminColumns = [
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
      title: 'Verificado',
      dataIndex: 'is_verified',
      key: 'is_verified',
      render: (isVerified: boolean) => (
        <Tag color={isVerified ? 'success' : 'warning'}>
          {isVerified ? 'Si' : 'No'}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Fecha de Creacion',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (record: SuperAdminUser) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => openEditSuperAdminModal(record)}
          >
            Editar
          </Button>
          <Popconfirm
            title={record.is_active ? "¿Desactivar este super admin?" : "¿Activar este super admin?"}
            onConfirm={() => handleActivateDeactivateSuperAdmin(record.id, !record.is_active)}
            okText="Si"
            cancelText="No"
          >
            <Button icon={record.is_active ? <StopOutlined /> : <CheckCircleOutlined />}>
              {record.is_active ? 'Desactivar' : 'Activar'}
            </Button>
          </Popconfirm>
          <Button danger disabled icon={<DeleteOutlined />}>
            Borrar
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ color: '#1B365D', marginBottom: 24 }}>
        Panel de Administración Superior
      </Title>

      <Tabs 
        defaultActiveKey="tenants" 
        style={{ marginBottom: 24 }}
      >
        <TabPane tab="Tenants" key="tenants">
          <Card
            title="Gestión de Tenants"
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={openCreateTenantModal}
              >
                Nuevo Tenant
              </Button>
            }
          >
            <Table 
              dataSource={tenants} 
              columns={tenantColumns} 
              rowKey="id" 
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Corporaciones" key="corporations">
          <Card
            title="Gestión de Corporaciones"
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={openCreateCorporationModal}
              >
                Nueva Corporación
              </Button>
            }
          >
            <Table 
              dataSource={corporations} 
              columns={corporationColumns} 
              rowKey="id" 
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Licencias" key="licenses">
          <Card
            title="Gestión de Licencias"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setShowLicenseModal(true)}
              >
                Nueva Licencia
              </Button>
            }
          >
            <Table 
              dataSource={licenses} 
              columns={licenseColumns} 
              rowKey="id" 
              loading={loading}
            />
          </Card>
        </TabPane>

        <TabPane tab="Super admins" key="super-admins">
          <Card
            title="Super administradores"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={openCreateSuperAdminModal}
              >
                Nuevo Super Admin
              </Button>
            }
          >
            <Table
              dataSource={superAdmins}
              columns={superAdminColumns}
              rowKey="id"
              loading={loading}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Modals */}
      <Modal
        title={editingTenant ? 'Editar Tenant' : 'Crear Nuevo Tenant'}
        open={showTenantModal}
        onCancel={() => {
          setShowTenantModal(false);
          setEditingTenant(null);
          tenantForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={tenantForm}
          layout="vertical"
          onFinish={handleSaveTenant}
        >
          <AntdForm.Item
            name="name"
            label="Nombre del Tenant"
            rules={[{ required: true, message: 'Por favor ingrese el nombre del tenant' }]}
          >
            <Input id="tenant-name-input" placeholder="Ej: Empresa ABC S.A." />
          </AntdForm.Item>
          
          <AntdForm.Item
            name="subdomain"
            label="Subdominio"
            rules={[{ required: true, message: 'Por favor ingrese el subdominio' }]}
          >
            <Input id="tenant-subdomain-input" placeholder="Ej: empresaabc" />
          </AntdForm.Item>
          
          <AntdForm.Item
            name="contact_email"
            label="Correo de Contacto"
            rules={[
              { required: true, message: 'Por favor ingrese el correo de contacto' },
              { type: 'email', message: 'Ingrese un correo electrónico válido' }
            ]}
          >
            <Input id="tenant-email-input" placeholder="Ej: contacto@empresaabc.com" />
          </AntdForm.Item>

          <AntdForm.Item
            name="contact_phone"
            label="Telefono de Contacto"
          >
            <Input id="tenant-phone-input" placeholder="Ej: +52 999 123 4567" />
          </AntdForm.Item>

          <AntdForm.Item
            name="grupo_corporativo_id"
            label="Corporacion"
          >
            <Select allowClear placeholder="Empresa independiente">
              {corporations.map((corporation) => (
                <Select.Option key={corporation.id} value={corporation.id}>
                  {corporation.name}
                </Select.Option>
              ))}
            </Select>
          </AntdForm.Item>
          
          <AntdForm.Item
            name="descripcion"
            label="Descripción"
          >
            <Input.TextArea id="tenant-desc-input" placeholder="Breve descripción del tenant..." />
          </AntdForm.Item>
          
          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              {editingTenant ? 'Guardar Tenant' : 'Crear Tenant'}
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title="Asignar tenant a corporacion"
        open={showAssignCorporationModal}
        onCancel={() => {
          setShowAssignCorporationModal(false);
          setSelectedTenant(null);
          assignCorporationForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={assignCorporationForm}
          layout="vertical"
          onFinish={handleAssignCorporation}
        >
          <AntdForm.Item
            name="corporation_id"
            label="Corporacion"
            rules={[{ required: true, message: 'Selecciona una corporacion' }]}
          >
            <Select placeholder="Selecciona corporacion">
              {corporations.map((corporation) => (
                <Select.Option key={corporation.id} value={corporation.id}>
                  {corporation.name}
                </Select.Option>
              ))}
            </Select>
          </AntdForm.Item>

          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              Asignar corporacion
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title={`Empresas de ${selectedCorporation?.name || 'corporacion'}`}
        open={showCorporationTenantsModal}
        onCancel={() => {
          setShowCorporationTenantsModal(false);
          setSelectedCorporation(null);
        }}
        footer={null}
        width={900}
        destroyOnClose
      >
        <Table
          dataSource={getCorporationTenants(selectedCorporation?.id)}
          rowKey="id"
          pagination={false}
          columns={[
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
              render: (isActive: boolean) => (
                <Tag color={isActive ? 'success' : 'error'}>
                  {isActive ? 'Activo' : 'Inactivo'}
                </Tag>
              ),
            },
          ]}
        />
      </Modal>

      <Modal
        title={`Asignar empresas a ${selectedCorporation?.name || 'corporacion'}`}
        open={showManageCorporationTenantsModal}
        onCancel={() => {
          setShowManageCorporationTenantsModal(false);
          setSelectedCorporation(null);
          manageCorporationTenantsForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={manageCorporationTenantsForm}
          layout="vertical"
          onFinish={handleManageCorporationTenants}
        >
          <AntdForm.Item
            name="tenant_ids"
            label="Empresas"
          >
            <Select
              mode="multiple"
              allowClear
              placeholder="Selecciona una o mas empresas"
              optionFilterProp="label"
              options={tenants.map((tenant) => ({
                label: `${tenant.name} (${tenant.subdomain})`,
                value: tenant.id,
              }))}
            />
          </AntdForm.Item>

          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              Guardar empresas
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title={editingCorporation ? 'Editar Corporacion' : 'Crear Nueva Corporacion'}
        open={showCorporationModal}
        onCancel={() => {
          setShowCorporationModal(false);
          setEditingCorporation(null);
          corporationForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={corporationForm}
          layout="vertical"
          onFinish={editingCorporation ? handleSaveCorporation : handleCreateCorporation}
        >
          <AntdForm.Item
            name="name"
            label="Nombre de la Corporación"
            rules={[{ required: true, message: 'Por favor ingrese el nombre de la corporación' }]}
          >
            <Input id="corp-name-input" placeholder="Ej: Grupo Empresarial XYZ" />
          </AntdForm.Item>
          
          <AntdForm.Item
            name="descripcion"
            label="Descripción"
          >
            <Input.TextArea id="corp-desc-input" placeholder="Breve descripción de la corporación..." />
          </AntdForm.Item>
          
          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              {editingCorporation ? 'Guardar Corporacion' : 'Crear Corporacion'}
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title="Crear Nueva Licencia"
        open={showLicenseModal}
        onCancel={() => {
          setShowLicenseModal(false);
          licenseForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={licenseForm}
          layout="vertical"
          onFinish={handleCreateLicense}
        >
          <AntdForm.Item
            name="tenant_id"
            label="Tenant"
            rules={[{ required: true, message: 'Selecciona el tenant' }]}
          >
            <Select placeholder="Selecciona tenant">
              {tenants.map((tenant) => (
                <Select.Option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </Select.Option>
              ))}
            </Select>
          </AntdForm.Item>

          <AntdForm.Item
            name="tipo_licencia_id"
            label="Tipo de licencia"
            rules={[{ required: true, message: 'Selecciona el tipo de licencia' }]}
          >
            <Select placeholder="Selecciona tipo de licencia">
              {licenseTypes.map((tipo) => (
                <Select.Option key={tipo.id} value={tipo.id}>
                  {tipo.nombre} ({tipo.duracion_dias} dias)
                </Select.Option>
              ))}
            </Select>
          </AntdForm.Item>

          <AntdForm.Item
            name="notas"
            label="Notas"
          >
            <Input.TextArea placeholder="Notas internas de la licencia..." />
          </AntdForm.Item>

          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              Crear Licencia
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title={editingSuperAdmin ? 'Editar Super Admin' : 'Crear Super Admin'}
        open={showSuperAdminModal}
        onCancel={() => {
          setShowSuperAdminModal(false);
          setEditingSuperAdmin(null);
          superAdminForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={superAdminForm}
          layout="vertical"
          onFinish={editingSuperAdmin ? handleSaveSuperAdmin : handleCreateSuperAdmin}
        >
          <AntdForm.Item
            name="nombre_completo"
            label="Nombre completo"
            rules={[{ required: true, message: 'Ingresa el nombre completo' }]}
          >
            <Input placeholder="Ej: Maria Admin" />
          </AntdForm.Item>

          <AntdForm.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Ingresa el email' },
              { type: 'email', message: 'Ingresa un email valido' }
            ]}
          >
            <Input placeholder="admin@guayabera-erp.com" />
          </AntdForm.Item>

          <AntdForm.Item
            name="password"
            label={editingSuperAdmin ? 'Nueva contrasena' : 'Contrasena temporal'}
            rules={editingSuperAdmin ? [] : [{ required: true, message: 'Ingresa una contrasena temporal' }]}
          >
            <Input.Password placeholder={editingSuperAdmin ? 'Dejar en blanco para conservarla' : 'Contrasena temporal'} />
          </AntdForm.Item>

          {editingSuperAdmin && (
            <>
              <AntdForm.Item
                name="is_verified"
                label="Verificado"
                valuePropName="checked"
              >
                <Switch />
              </AntdForm.Item>

              <AntdForm.Item
                name="is_active"
                label="Activo"
                valuePropName="checked"
              >
                <Switch />
              </AntdForm.Item>
            </>
          )}

          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              {editingSuperAdmin ? 'Guardar Super Admin' : 'Crear Super Admin'}
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>

      <Modal
        title="Invitar Administrador de Tenant"
        open={!!showInviteModal}
        onCancel={() => {
          setShowInviteModal(false);
          setSelectedTenant(null);
          inviteForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <AntdForm
          form={inviteForm}
          layout="vertical"
          onFinish={handleInviteAdmin}
        >
          <AntdForm.Item
            name="email"
            label="Correo Electrónico del Administrador"
            rules={[
              { required: true, message: 'Por favor ingrese el correo electrónico' },
              { type: 'email', message: 'Ingrese un correo electrónico válido' }
            ]}
          >
            <Input id="admin-email-input" placeholder="Ej: admin@empresacliente.com" />
          </AntdForm.Item>
          
          <AntdForm.Item>
            <Button type="primary" htmlType="submit" block>
              Enviar Invitación
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </Modal>
    </div>
  );
};

export default SuperAdminDashboard;
