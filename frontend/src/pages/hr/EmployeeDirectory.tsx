import React, { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Modal, Form, Input, Select, message, Space, Tabs, Row, Col } from 'antd';
import { TeamOutlined, UserAddOutlined, ClusterOutlined, UploadOutlined, FileTextOutlined } from '@ant-design/icons';
import { hrService, Empleado, Departamento, ContratoLaboral } from '../../services/hrService';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

export const EmployeeDirectory: React.FC = () => {
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [departamentos, setDepartamentos] = useState<Departamento[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  
  const [isExpedienteVisible, setIsExpedienteVisible] = useState(false);
  const [isContratoVisible, setIsContratoVisible] = useState(false);
  const [selectedEmpleado, setSelectedEmpleado] = useState<Empleado | null>(null);
  const [contratoForm] = Form.useForm();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [emps, depts] = await Promise.all([
        hrService.getEmpleados(),
        hrService.getDepartamentos()
      ]);
      setEmpleados(emps);
      setDepartamentos(depts);
    } catch (error) {
      message.error("Error cargando datos del directorio");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateEmpleado = async (values: any) => {
    try {
      await hrService.createEmpleado(values);
      message.success("Empleado registrado exitosamente");
      setIsModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al registrar empleado");
    }
  };

  const handleOpenExpediente = (record: Empleado) => {
    setSelectedEmpleado(record);
    setIsExpedienteVisible(true);
  };

  const handleOpenContrato = (record: Empleado) => {
    setSelectedEmpleado(record);
    setIsContratoVisible(true);
    contratoForm.resetFields();
  };

  const handleSaveContrato = async (values: any) => {
    if (!selectedEmpleado) return;
    try {
      await hrService.createContrato({
        ...values,
        empleado_id: selectedEmpleado.id,
        fecha_inicio: values.fecha_inicio.format('YYYY-MM-DD'),
        fecha_fin: values.fecha_fin ? values.fecha_fin.format('YYYY-MM-DD') : null
      });
      message.success("Contrato guardado exitosamente");
      setIsContratoVisible(false);
    } catch (error) {
      message.error("Error al guardar el contrato");
    }
  };

  const columns = [
    { title: 'Código', dataIndex: 'codigo', key: 'codigo' },
    { title: 'Nombre Completo', dataIndex: 'nombre_completo', key: 'nombre_completo' },
    { 
      title: 'Departamento', 
      key: 'departamento',
      render: (_: any, record: Empleado) => {
        const dep = departamentos.find(d => d.id === record.departamento_id);
        return dep ? dep.nombre : 'Sin Asignar';
      }
    },
    { title: 'Puesto', dataIndex: 'puesto', key: 'puesto' },
    {
      title: 'Jefe Inmediato',
      key: 'jefe',
      render: (_: any, record: Empleado) => {
        const jefe = empleados.find(e => e.id === record.jefe_id);
        return jefe ? jefe.nombre_completo : '-';
      }
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Empleado) => (
        <Space>
          <Button type="link" onClick={() => handleOpenExpediente(record)}>Expediente</Button>
          <Button type="link" icon={<FileTextOutlined />} onClick={() => handleOpenContrato(record)}>Contrato</Button>
        </Space>
      )
    }
  ];

  // Helper para dibujar Organigrama Básico en texto (Podríamos usar un componente de Tree, pero por ahora listas anidadas)
  const renderOrganigrama = (jefeId: string | null = null, level: number = 0) => {
    const subordinados = empleados.filter(e => (e.jefe_id || null) === jefeId);
    if (subordinados.length === 0) return null;

    return (
      <div style={{ paddingLeft: level * 20 }}>
        {subordinados.map(sub => (
          <div key={sub.id} style={{ marginBottom: '8px' }}>
            <Card size="small" style={{ width: '300px', backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }}>
              <Text strong style={{ color: 'var(--accent-primary)' }}>{sub.nombre_completo}</Text>
              <br />
              <Text type="secondary" style={{ fontSize: '12px' }}>{sub.puesto} | {departamentos.find(d=>d.id===sub.departamento_id)?.nombre}</Text>
            </Card>
            {renderOrganigrama(sub.id, level + 1)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <TeamOutlined /> Directorio y Organigrama
          </Title>
        </Col>
        <Col>
          <Button type="primary" icon={<UserAddOutlined />} onClick={() => setIsModalVisible(true)} style={{ backgroundColor: 'var(--accent-primary)' }}>
            Nuevo Empleado
          </Button>
        </Col>
      </Row>

      <Card style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}>
        <Tabs defaultActiveKey="1">
          <TabPane tab={<span><TeamOutlined /> Lista de Empleados</span>} key="1">
            <Table 
              dataSource={empleados} 
              columns={columns} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
          <TabPane tab={<span><ClusterOutlined /> Organigrama de la Empresa</span>} key="2">
            <div style={{ padding: '20px', overflowX: 'auto' }}>
              {/* Dibujamos a los que no tienen jefe como Raíz */}
              {renderOrganigrama(null, 0)}
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* Modal Nuevo Empleado */}
      <Modal
        title="Registrar Nuevo Empleado"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateEmpleado}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="codigo" label="Código Emp." rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item name="nombre_completo" label="Nombre Completo" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="departamento_id" label="Departamento">
                <Select placeholder="Seleccionar Depto">
                  {departamentos.map(d => <Option key={d.id} value={d.id}>{d.nombre}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="puesto" label="Puesto">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="jefe_id" label="Jefe Inmediato (Reporta a)">
            <Select showSearch optionFilterProp="children" placeholder="Seleccionar Jefe">
              {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
            </Select>
          </Form.Item>

          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)' }}>
            Guardar Empleado
          </Button>
        </Form>
      </Modal>

      {/* Modal Expediente Digital */}
      <Modal
        title={`Expediente Digital: ${selectedEmpleado?.nombre_completo}`}
        visible={isExpedienteVisible}
        onCancel={() => setIsExpedienteVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsExpedienteVisible(false)}>Cerrar</Button>
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>Documentos Requeridos:</Text>
          <Card size="small">
            <Row justify="space-between" align="middle">
              <Text>1. Contrato Firmado</Text>
              <Button size="small" icon={<UploadOutlined />}>Subir PDF</Button>
            </Row>
          </Card>
          <Card size="small">
            <Row justify="space-between" align="middle">
              <Text>2. Constancia de Situación Fiscal (RFC)</Text>
              <Button size="small" icon={<UploadOutlined />}>Subir PDF</Button>
            </Row>
          </Card>
          <Card size="small">
            <Row justify="space-between" align="middle">
              <Text>3. Alta del IMSS (NSS)</Text>
              <Button size="small" icon={<UploadOutlined />}>Subir PDF</Button>
            </Row>
          </Card>
          
          <div style={{ marginTop: '16px' }}>
            <Text type="secondary">Nota: La subida de documentos se guardará en Amazon S3 en futuras iteraciones. Por ahora es representativo del expediente.</Text>
          </div>
        </Space>
      </Modal>

      {/* Modal Contrato */}
      <Modal
        title={`Configurar Contrato: ${selectedEmpleado?.nombre_completo}`}
        visible={isContratoVisible}
        onCancel={() => setIsContratoVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={contratoForm} layout="vertical" onFinish={handleSaveContrato}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="tipo_contrato" label="Tipo de Contrato" rules={[{ required: true }]} initialValue="01">
                <Select>
                  <Option value="01">01 - Tiempo Indeterminado</Option>
                  <Option value="02">02 - Obra determinada</Option>
                  <Option value="03">03 - Tiempo determinado</Option>
                  <Option value="09">09 - Honorarios / Asimilados</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="tipo_jornada_id" label="Tipo de Jornada" rules={[{ required: true }]} initialValue="01">
                <Select>
                  <Option value="01">01 - Diurna</Option>
                  <Option value="02">02 - Nocturna</Option>
                  <Option value="03">03 - Mixta</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="periodicidad_pago_id" label="Periodicidad" rules={[{ required: true }]} initialValue="04">
                <Select>
                  <Option value="02">02 - Semanal</Option>
                  <Option value="04">04 - Quincenal</Option>
                  <Option value="05">05 - Mensual</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="salario_diario" label="Salario Diario ($)" rules={[{ required: true }]}>
                <Input type="number" step="0.01" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="salario_base_cotizacion" label="SBC (IMSS)">
                <Input type="number" step="0.01" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="dias_laborables" label="Días Laborables/Semana" rules={[{ required: true }]} initialValue={6}>
                <Input type="number" min={1} max={7} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="fecha_inicio" label="Fecha de Inicio" rules={[{ required: true }]}>
                {/* Asumiremos que tienen moment/dayjs o pondrán un datepicker real, por ahora DatePicker de antd */}
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>

          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)' }}>
            Guardar Contrato Laboral
          </Button>
        </Form>
      </Modal>

      <style>{`
        .dark-table .ant-table { background-color: transparent !important; color: var(--text-main) !important; }
        .dark-table .ant-table-thead > tr > th { background-color: var(--bg-main) !important; color: var(--text-secondary) !important; border-bottom: 1px solid var(--border-color); }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid var(--border-color); }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: var(--bg-main) !important; }
      `}</style>
    </div>
  );
};
