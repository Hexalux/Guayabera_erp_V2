import React, { useEffect, useState } from 'react';
import { Button, Card, Empty, Form, Input, Modal, Select, Table, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
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

interface LicenseType {
  id: string;
  nombre: string;
  duracion_dias: number;
  precio?: number;
}

const LicensesList: React.FC = () => {
  const [licenses, setLicenses] = useState<TenantLicense[]>([]);
  const [activeLicense, setActiveLicense] = useState<TenantLicense | null>(null);
  const [licenseTypes, setLicenseTypes] = useState<LicenseType[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchLicenses = async () => {
    setLoading(true);
    try {
      const [summaryRes, licenseTypesRes] = await Promise.all([
        api.get('/tenant-portal/resumen'),
        api.get('/tenant-portal/tipos-licencia'),
      ]);
      setLicenses(summaryRes.data.licencias);
      setActiveLicense(summaryRes.data.licencia_activa);
      setLicenseTypes(licenseTypesRes.data.tipos_licencia);
    } catch (error: any) {
      message.error(getApiErrorMessage(error, 'Error al cargar licencias'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicenses();
  }, []);

  const handleRequestLicense = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/tenant-portal/solicitar-licencia', values);
      message.success('Solicitud enviada al super-admin');
      setModalVisible(false);
      form.resetFields();
      fetchLicenses();
    } catch (error: any) {
      if (error?.errorFields) {
        return;
      }
      message.error(getApiErrorMessage(error, 'Error al solicitar licencia'));
    }
  };

  const columns = [
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
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'warning'}>
          {isActive ? 'Activa' : 'Pendiente'}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, textAlign: 'left' }}>
      <Card
        title="Licencia activa"
        loading={loading}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            Solicitar licencia
          </Button>
        }
      >
        {activeLicense ? (
          <>
            <p><strong>Tipo:</strong> {activeLicense.tipo_licencia_nombre || activeLicense.codigo}</p>
            <p><strong>Activacion:</strong> {dayjs(activeLicense.fecha_inicio).format('YYYY-MM-DD')}</p>
            <p><strong>Vencimiento:</strong> {dayjs(activeLicense.fecha_fin).format('YYYY-MM-DD')}</p>
            <Tag color="green">Activa</Tag>
          </>
        ) : (
          <Empty description="No hay licencia activa" />
        )}
      </Card>

      <Card title="Historial de licencias" style={{ marginTop: 16 }} loading={loading}>
        <Table dataSource={licenses} columns={columns} rowKey="id" />
      </Card>

      <Modal
        title="Solicitar nueva licencia"
        open={modalVisible}
        onOk={handleRequestLicense}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        okText="Enviar solicitud"
        cancelText="Cancelar"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
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
            <Input.TextArea placeholder="Describe la necesidad de la licencia..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LicensesList;
