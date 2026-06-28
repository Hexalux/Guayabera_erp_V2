import React, { useState, useEffect } from 'react';
import { Typography, Tabs, Form, Input, Switch, Button, Checkbox, Space, Table, Modal, message, Card, Spin } from 'antd';
import { SaveOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { api } from '../../services/authService';

const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;

interface SalesConfigData {
  id?: string;
  encabezado_ticket: string;
  pie_ticket: string;
  permite_credito: boolean;
  metodos_pago_permitidos: string;
  equipos_ventas: string;
}

export const SalesConfig: React.FC = () => {
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'ajustes';
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<SalesConfigData | null>(null);
  const [form] = Form.FormInstance ? [Form.useForm()[0]] : Form.useForm();
  
  // Equipos de Ventas
  const [equipos, setEquipos] = useState<Array<{ id: string; nombre: string; lider: string }>>([]);
  const [isEquipoModalVisible, setIsEquipoModalVisible] = useState(false);
  const [nuevoEquipoNombre, setNuevoEquipoNombre] = useState('');
  const [nuevoEquipoLider, setNuevoEquipoLider] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const res = await api.get('/sales/configuracion');
      setConfig(res.data);
      form.setFieldsValue({
        encabezado_ticket: res.data.encabezado_ticket,
        pie_ticket: res.data.pie_ticket,
        permite_credito: res.data.permite_credito,
        metodos: res.data.metodos_pago_permitidos.split(','),
      });
      if (res.data.equipos_ventas) {
        setEquipos(JSON.parse(res.data.equipos_ventas));
      }
    } catch (error) {
      console.error('Error cargando configuración', error);
      message.error('No se pudo cargar la configuración de ventas.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (values: any) => {
    try {
      setSaving(true);
      const payload = {
        encabezado_ticket: values.encabezado_ticket,
        pie_ticket: values.pie_ticket,
        permite_credito: values.permite_credito,
        metodos_pago_permitidos: values.metodos.join(','),
        equipos_ventas: JSON.stringify(equipos),
      };
      const res = await api.put('/sales/configuracion', payload);
      setConfig(res.data);
      message.success('Configuración guardada exitosamente.');
    } catch (error) {
      console.error('Error guardando configuración', error);
      message.error('No se pudo guardar la configuración.');
    } finally {
      setSaving(false);
    }
  };

  const handleAddEquipo = () => {
    if (!nuevoEquipoNombre || !nuevoEquipoLider) {
      message.warning('Por favor completa todos los campos.');
      return;
    }
    const nuevo = {
      id: Math.random().toString(36).substr(2, 9),
      nombre: nuevoEquipoNombre,
      lider: nuevoEquipoLider,
    };
    const nuevosEquipos = [...equipos, nuevo];
    setEquipos(nuevosEquipos);
    setIsEquipoModalVisible(false);
    setNuevoEquipoNombre('');
    setNuevoEquipoLider('');
    
    // Auto guardado de equipos
    if (config) {
      handleSaveConfig({
        encabezado_ticket: form.getFieldValue('encabezado_ticket'),
        pie_ticket: form.getFieldValue('pie_ticket'),
        permite_credito: form.getFieldValue('permite_credito'),
        metodos: form.getFieldValue('metodos') || [],
      });
    }
  };

  const handleDeleteEquipo = (id: string) => {
    const nuevosEquipos = equipos.filter(e => e.id !== id);
    setEquipos(nuevosEquipos);
    message.info('Equipo removido de la lista temporal. Haz clic en guardar para confirmar.');
  };

  if (loading || !config) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', backgroundColor: '#0C0E14' }}>
        <Spin size="large" />
      </div>
    );
  }

  const columnsEquipos = [
    { title: 'Nombre del Equipo', dataIndex: 'nombre', key: 'nombre', render: (text: string) => <span style={{ color: '#FFF' }}>{text}</span> },
    { title: 'Líder / Supervisor', dataIndex: 'lider', key: 'lider', render: (text: string) => <span style={{ color: '#B8B9BD' }}>{text}</span> },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: any) => (
        <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDeleteEquipo(record.id)} />
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF', textAlign: 'left' }}>
      <Title level={2} style={{ color: '#00A651', marginBottom: '24px' }}>Configuración del Canal de Ventas</Title>

      <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveConfig}
          initialValues={{
            metodos: ['EFECTIVO', 'TARJETA', 'TRANSFERENCIA']
          }}
        >
          <Tabs defaultActiveKey={activeTab} className="dark-tabs">
            {/* Ajustes Generales */}
            <TabPane tab="Ajustes" key="ajustes">
              <div style={{ padding: '16px 0' }}>
                <Form.Item name="permite_credito" label={<span style={{ color: '#FFF' }}>Permitir Ventas a Crédito (CxC)</span>} valuePropName="checked">
                  <Switch checkedChildren="Sí" unCheckedChildren="No" />
                </Form.Item>
                <Paragraph style={{ color: '#B8B9BD' }}>
                  Habilita el cobro con la opción de Crédito (generando cuentas por cobrar automáticas en TutConta).
                </Paragraph>
              </div>
            </TabPane>

            {/* Equipos de ventas */}
            <TabPane tab="Equipos de Ventas" key="equipos">
              <div style={{ padding: '16px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <span style={{ color: '#B8B9BD' }}>Administra los supervisores y equipos comerciales.</span>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsEquipoModalVisible(true)} style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}>
                    Nuevo Equipo
                  </Button>
                </div>
                <Table
                  dataSource={equipos}
                  columns={columnsEquipos}
                  rowKey="id"
                  pagination={false}
                  className="dark-table"
                />
              </div>
            </TabPane>

            {/* Encabezados y pies de ticket */}
            <TabPane tab="Encabezados/Pies" key="encabezados">
              <div style={{ padding: '16px 0' }}>
                <Form.Item name="encabezado_ticket" label={<span style={{ color: '#FFF' }}>Encabezado del Ticket POS</span>}>
                  <Input.TextArea rows={3} style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                </Form.Item>
                <Form.Item name="pie_ticket" label={<span style={{ color: '#FFF' }}>Pie de Página del Ticket POS</span>}>
                  <Input.TextArea rows={3} style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                </Form.Item>
              </div>
            </TabPane>

            {/* Métodos de Pago */}
            <TabPane tab="Métodos de Pago" key="metodos">
              <div style={{ padding: '16px 0' }}>
                <Form.Item name="metodos" label={<span style={{ color: '#FFF' }}>Métodos de Pago Autorizados</span>}>
                  <Checkbox.Group style={{ width: '100%' }}>
                    <Space direction="vertical">
                      <Checkbox value="EFECTIVO" style={{ color: '#FFF' }}>Efectivo en Caja</Checkbox>
                      <Checkbox value="TARJETA" style={{ color: '#FFF' }}>Tarjeta Bancaria (Terminal)</Checkbox>
                      <Checkbox value="TRANSFERENCIA" style={{ color: '#FFF' }}>Transferencia SPEI</Checkbox>
                      <Checkbox value="CRÉDITO" style={{ color: '#FFF' }}>Crédito Comercial (CxC)</Checkbox>
                    </Space>
                  </Checkbox.Group>
                </Form.Item>
              </div>
            </TabPane>
          </Tabs>

          <Form.Item style={{ marginTop: '24px' }}>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving} style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}>
              Guardar Configuración
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Modal
        title="Agregar Nuevo Equipo de Ventas"
        open={isEquipoModalVisible}
        onOk={handleAddEquipo}
        onCancel={() => setIsEquipoModalVisible(false)}
        okText="Agregar"
        cancelText="Cancelar"
        bodyStyle={{ backgroundColor: '#161A24', padding: '16px 0' }}
        className="dark-modal"
      >
        <div style={{ marginBottom: '16px' }}>
          <span style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Nombre del Equipo:</span>
          <Input value={nuevoEquipoNombre} onChange={e => setNuevoEquipoNombre(e.target.value)} placeholder="Ej. Ventas Mayoreo Sureste" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
        </div>
        <div>
          <span style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Líder / Supervisor responsable:</span>
          <Input value={nuevoEquipoLider} onChange={e => setNuevoEquipoLider(e.target.value)} placeholder="Ej. Lic. Carlos Mendoza" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
        </div>
      </Modal>

      <style>{`
        .dark-tabs .ant-tabs-nav {
          border-bottom: 1px solid #303030 !important;
        }
        .dark-tabs .ant-tabs-tab {
          color: #B8B9BD !important;
        }
        .dark-tabs .ant-tabs-tab-active {
          color: #00A651 !important;
        }
        .dark-tabs .ant-tabs-ink-bar {
          background-color: #00A651 !important;
        }
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
        .ant-modal-content {
          background-color: #161A24 !important;
        }
        .ant-modal-header {
          background-color: #161A24 !important;
          border-bottom: 1px solid #303030 !important;
        }
        .ant-modal-title {
          color: #FFF !important;
        }
      `}</style>
    </div>
  );
};
