import React, { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Row, Col, Modal, Form, Select, DatePicker, InputNumber, message, Tag, Space, Divider, List } from 'antd';
import { DollarOutlined, PlusOutlined, CalculatorOutlined, FilePdfOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { hrService, Nomina, Empleado, ContratoLaboral } from '../../services/hrService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

export const Payroll: React.FC = () => {
  const [nominas, setNominas] = useState<Nomina[]>([]);
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isCalcModalVisible, setIsCalcModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [calcForm] = Form.useForm();
  const [selectedContrato, setSelectedContrato] = useState<ContratoLaboral | null>(null);
  const [diasPeriodo, setDiasPeriodo] = useState<number>(15);
  const [faltas, setFaltas] = useState<number>(0);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [noms, emps] = await Promise.all([
        hrService.getNominas(),
        hrService.getEmpleados()
      ]);
      setNominas(noms);
      setEmpleados(emps);
    } catch (error) {
      message.error("Error cargando registros de nómina");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateNomina = async (values: any) => {
    try {
      const neto_pagado = (values.total_percepciones || 0) - (values.total_deducciones || 0);
      await hrService.createNomina({
        ...values,
        fecha_pago: values.fecha_pago.format('YYYY-MM-DD'),
        neto_pagado
      });
      message.success("Registro de nómina creado");
      setIsModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al registrar nómina");
    }
  };

  const reCalculate = async (dias: number, f: number) => {
    if (selectedContrato && calcForm.getFieldValue('empleado_id_calc')) {
      try {
        const empId = calcForm.getFieldValue('empleado_id_calc');
        const calcRes = await hrService.calcularNomina({
          empleado_id: empId,
          dias_periodo: dias,
          faltas: f
        });
        
        calcForm.setFieldsValue({
          total_percepciones: calcRes.total_percepciones,
          total_deducciones: calcRes.total_deducciones,
          isr_retenido: calcRes.isr_retenido,
          cuota_imss: calcRes.cuota_imss
        });
        message.success("Cálculo actualizado según Tablas SAT");
      } catch (e) {
        message.error("Error al calcular con el motor backend");
      }
    }
  };

  const handleSelectEmpleadoParaCalculo = async (empleadoId: string) => {
    try {
      const contratos = await hrService.getContratosEmpleado(empleadoId);
      if (contratos && contratos.length > 0) {
        setSelectedContrato(contratos[0]);
        calcForm.setFieldsValue({ empleado_id_calc: empleadoId });
        await reCalculate(diasPeriodo, faltas);
      } else {
        setSelectedContrato(null);
        message.warning("El empleado no tiene un contrato configurado.");
      }
    } catch (error) {
      message.error("Error al obtener el contrato del empleado.");
    }
  };

  const handleSaveCalculo = async (values: any) => {
    try {
      const neto_pagado = (values.total_percepciones || 0) - (values.total_deducciones || 0);
      await hrService.createNomina({
        empleado_id: values.empleado_id_calc,
        fecha_pago: values.fecha_pago_calc.format('YYYY-MM-DD'),
        total_percepciones: values.total_percepciones,
        total_deducciones: values.total_deducciones,
        neto_pagado
      });
      message.success("Nómina preliminar calculada y guardada.");
      setIsCalcModalVisible(false);
      calcForm.resetFields();
      setSelectedContrato(null);
      fetchData();
    } catch (error) {
      message.error("Error al guardar la nómina calculada");
    }
  };

  const handleTimbrar = async (nominaId: string) => {
    try {
      message.loading({ content: 'Conectando con el PAC...', key: 'timbrado' });
      await hrService.timbrarNomina(nominaId);
      message.success({ content: '¡Nómina Timbrada Exitosamente!', key: 'timbrado', duration: 2 });
      fetchData();
    } catch (error) {
      message.error({ content: 'Error en el PAC al timbrar la nómina.', key: 'timbrado', duration: 3 });
    }
  };

  const columns = [
    {
      title: 'Empleado',
      key: 'empleado',
      render: (_: any, record: Nomina) => {
        const emp = empleados.find(e => e.id === record.empleado_id);
        return emp ? emp.nombre_completo : 'Desconocido';
      }
    },
    { title: 'Fecha Pago', dataIndex: 'fecha_pago', key: 'fecha_pago' },
    { title: 'Percepciones', dataIndex: 'total_percepciones', key: 'percepciones', render: (val: number) => `$${val.toFixed(2)}` },
    { title: 'Deducciones', dataIndex: 'total_deducciones', key: 'deducciones', render: (val: number) => `$${val.toFixed(2)}` },
    { title: 'Neto Pagado', dataIndex: 'neto_pagado', key: 'neto_pagado', render: (val: number) => <Text style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>${val.toFixed(2)}</Text> },
    {
      title: 'Estado CFDI',
      dataIndex: 'estado_timbrado',
      key: 'estado_timbrado',
      render: (estado: string) => {
        let color = 'default';
        if (estado === 'TIMBRADO') color = 'success';
        if (estado === 'ERROR') color = 'error';
        if (estado === 'PENDIENTE') color = 'processing';
        return <Tag color={color}>{estado ? estado.toUpperCase() : 'PENDIENTE'}</Tag>;
      }
    },
    {
      title: 'Acciones CFDI',
      key: 'acciones_cfdi',
      render: (_: any, record: Nomina) => {
        if (record.estado_timbrado === 'TIMBRADO') {
          return (
            <Space>
              <Button type="link" size="small" icon={<FilePdfOutlined />} onClick={() => window.open(record.url_pdf, '_blank')}>PDF</Button>
            </Space>
          );
        } else {
          return (
            <Button 
              type="primary" 
              size="small" 
              icon={<CheckCircleOutlined />} 
              onClick={() => handleTimbrar(record.id)}
              style={{ backgroundColor: 'var(--accent-primary)' }}
            >
              Timbrar SAT
            </Button>
          );
        }
      }
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <DollarOutlined /> Control de Nómina (Manual)
          </Title>
        </Col>
        <Col>
          <Space>
            <Button icon={<CalculatorOutlined />} onClick={() => setIsCalcModalVisible(true)} style={{ borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}>
              Motor de Cálculo
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)} style={{ backgroundColor: 'var(--accent-primary)' }}>
              Pago Manual
            </Button>
          </Space>
        </Col>
      </Row>

      <Card style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}>
        <Text style={{ display: 'block', marginBottom: '16px', color: 'var(--text-secondary)' }}>
          Nota: El cálculo de impuestos automáticos y el timbrado electrónico se integrará en el módulo fiscal. Este panel permite registrar pagos de nómina manuales para control interno.
        </Text>
        <Table
          dataSource={nominas}
          columns={columns}
          rowKey="id"
          loading={loading}
          className="dark-table"
        />
      </Card>

      <Modal
        title="Registrar Pago de Nómina"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateNomina}>
          <Form.Item name="empleado_id" label="Empleado" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
            </Select>
          </Form.Item>
          
          <Form.Item name="fecha_pago" label="Fecha de Pago" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="total_percepciones" label="Percepciones (Sueldo, Bonos)" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} prefix="$" min={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="total_deducciones" label="Deducciones (Préstamos, Faltas)" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} prefix="$" min={0} />
              </Form.Item>
            </Col>
          </Row>

          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)' }}>
            Guardar Registro Manual
          </Button>
        </Form>
      </Modal>

      <Modal
        title="Motor de Cálculo de Nómina"
        visible={isCalcModalVisible}
        onCancel={() => { setIsCalcModalVisible(false); setSelectedContrato(null); }}
        footer={null}
        width={700}
      >
        <Form form={calcForm} layout="vertical" onFinish={handleSaveCalculo}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="empleado_id_calc" label="Empleado" rules={[{ required: true }]}>
                <Select showSearch optionFilterProp="children" onChange={handleSelectEmpleadoParaCalculo}>
                  {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="fecha_pago_calc" label="Fecha de Cierre/Pago" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Parámetros del Periodo</Divider>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Salario Diario (Contrato)">
                <InputNumber disabled style={{ width: '100%' }} prefix="$" value={selectedContrato?.salario_diario || 0} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Días del Periodo">
                <InputNumber 
                  style={{ width: '100%' }} 
                  value={diasPeriodo} 
                  onChange={(val) => { setDiasPeriodo(val || 0); reCalculate(val || 0, faltas); }} 
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Inasistencias (Faltas)">
                <InputNumber 
                  style={{ width: '100%' }} 
                  value={faltas} 
                  onChange={(val) => { setFaltas(val || 0); reCalculate(diasPeriodo, val || 0); }} 
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Totalización CFDI 4.0</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="total_percepciones" label="Total Percepciones (Ingreso Gravable)">
                <InputNumber style={{ width: '100%' }} prefix="$" disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="total_deducciones" label="Total Deducciones (Impuestos + Faltas)">
                <InputNumber style={{ width: '100%' }} prefix="$" disabled />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="isr_retenido" label="Retención ISR (Automático)">
                <InputNumber style={{ width: '100%' }} prefix="$" disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cuota_imss" label="Cuota IMSS Obrero (Automático)">
                <InputNumber style={{ width: '100%' }} prefix="$" disabled />
              </Form.Item>
            </Col>
          </Row>

          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)', marginTop: '16px' }}>
            Autorizar Nómina y Guardar
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
