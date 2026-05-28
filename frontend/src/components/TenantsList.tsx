import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, message } from 'antd';
import { api, getApiErrorMessage } from '../services/authService';

interface Company {
  id: string;
  name: string;
  subdomain: string;
  contact_email?: string;
  contact_phone?: string;
  descripcion?: string;
  is_active: boolean;
}

interface TenantInfo extends Company {
  es_grupo_corporativo: boolean;
}

const TenantsList: React.FC = () => {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/tenant-portal/resumen');
      setTenant(response.data.tenant);
      setCompanies(response.data.empresas);
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al cargar empresas'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const columns = [
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
      title: 'Telefono',
      dataIndex: 'contact_phone',
      key: 'contact_phone',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Activa' : 'Inactiva'}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, textAlign: 'left' }}>
      <Card title="Empresa principal" loading={loading}>
        {tenant && (
          <>
            <p><strong>Nombre:</strong> {tenant.name}</p>
            <p><strong>Subdominio:</strong> {tenant.subdomain}</p>
            <p><strong>Contacto:</strong> {tenant.contact_email || 'Sin contacto'}</p>
            <Tag color={tenant.is_active ? 'green' : 'red'}>{tenant.is_active ? 'Activa' : 'Inactiva'}</Tag>
            {tenant.es_grupo_corporativo && <Tag color="blue">Grupo corporativo</Tag>}
          </>
        )}
      </Card>

      <Card title="Empresas configuradas" style={{ marginTop: 16 }} loading={loading}>
        <Table dataSource={companies} columns={columns} rowKey="id" />
      </Card>
    </div>
  );
};

export default TenantsList;
