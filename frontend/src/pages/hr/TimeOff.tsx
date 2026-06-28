import React, { useEffect, useState } from 'react';
import { Card, Typography, Tabs, Table, Button, Modal, Form, DatePicker, Select, Input, message, Tag, Row, Col } from 'antd';
import { CalendarOutlined, FrownOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { hrService, ControlVacaciones, Inasistencia, Empleado } from '../../services/hrService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;

export const TimeOff: React.FC = () => {
  const [vacaciones, setVacaciones] = useState<ControlVacaciones[]>([]);
  const [inasistencias, setInasistencias] = useState<Inasistencia[]>([]);
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [isVacModalVisible, setIsVacModalVisible] = useState(false);
  const [isInaModalVisible, setIsInaModalVisible] = useState(false);
  const [formVac] = Form.useForm();
  const [formIna] = Form.useForm();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [vacs, inas, emps] = await Promise.all([
        hrService.getVacaciones(),
        hrService.getInasistencias(),
        hrService.getEmpleados()
      ]);
      setVacaciones(vacs);
      setInasistencias(inas);
      setEmpleados(emps);
    } catch (error) {
      message.error("Error cargando datos de control de tiempos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRequestVacation = async (values: any) => {
    try {
      const [start, end] = values.fechas;
      const dias = end.diff(start, 'day') + 1; // Asumiendo días naturales para MVP
      
      await hrService.requestVacaciones({
        empleado_id: values.empleado_id,
        fecha_inicio: start.format('YYYY-MM-DD'),
        fecha_fin: end.format('YYYY-MM-DD'),
        dias_solicitados: dias
      });
      message.success("Solicitud de vacaciones enviada");
      setIsVacModalVisible(false);
      formVac.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al solicitar vacaciones");
    }
  };

  const handleRegisterInasistencia = async (values: any) => {
    try {
      await hrService.registrarInasistencia({
        empleado_id: values.empleado_id,
        fecha: values.fecha.format('YYYY-MM-DD'),
        motivo: values.motivo,
        justificada: values.justificada === 'true'
      });
      message.success("Inasistencia registrada");
      setIsInaModalVisible(false);
      formIna.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al registrar inasistencia");
    }
  };

  const updateVacStatus = async (id: string, action: 'approve' | 'reject') => {
    try {
      if(action === 'approve') await hrService.approveVacaciones(id);
      if(action === 'reject') await hrService.rejectVacaciones(id);
      message.success("Estado de solicitud actualizado");
      fetchData();
    } catch (error) {
      message.error("Error actualizando solicitud");
    }
  };

  const columnsVacaciones = [
    { 
      title: 'Empleado', 
      key: 'empleado',
      render: (_: any, r: ControlVacaciones) => empleados.find(e => e.id === r.empleado_id)?.nombre_completo 
    },
    { title: 'Del', dataIndex: 'fecha_inicio', key: 'fecha_inicio' },
    { title: 'Al', dataIndex: 'fecha_fin', key: 'fecha_fin' },
    { title: 'Días', dataIndex: 'dias_solicitados', key: 'dias_solicitados' },
    { 
      title: 'Estado', 
      dataIndex: 'estado', 
      key: 'estado',
      render: (estado: string) => {
        let color = 'gold';
        if (estado === 'aprobada') color = 'green';
        if (estado === 'rechazada') color = 'red';
        return <Tag color={color}>{estado.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Autorización',
      key: 'acciones',
      render: (_: any, r: ControlVacaciones) => r.estado === 'pendiente' ? (
        <>
          <Button type="text" icon={<CheckCircleOutlined style={{color:'green'}}/>} onClick={() => updateVacStatus(r.id, 'approve')} />
          <Button type="text" icon={<CloseCircleOutlined style={{color:'red'}}/>} onClick={() => updateVacStatus(r.id, 'reject')} />
        </>
      ) : null
    }
  ];

  const columnsInasistencias = [
    { 
      title: 'Empleado', 
      key: 'empleado',
      render: (_: any, r: Inasistencia) => empleados.find(e => e.id === r.empleado_id)?.nombre_completo 
    },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
    { title: 'Motivo', dataIndex: 'motivo', key: 'motivo' },
    { 
      title: 'Estatus', 
      dataIndex: 'justificada', 
      key: 'justificada',
      render: (just: boolean) => <Tag color={just ? 'blue' : 'red'}>{just ? 'Justificada' : 'Injustificada'}</Tag>
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <CalendarOutlined /> Vacaciones y Ausencias
          </Title>
        </Col>
      </Row>

      <Card style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}>
        <Tabs defaultActiveKey="1">
          <TabPane tab="Solicitudes de Vacaciones" key="1">
            <div style={{ marginBottom: '16px', textAlign: 'right' }}>
              <Button type="primary" onClick={() => setIsVacModalVisible(true)} style={{ backgroundColor: 'var(--accent-primary)' }}>Solicitar Vacaciones</Button>
            </div>
            <Table 
              dataSource={vacaciones} 
              columns={columnsVacaciones} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
            />
          </TabPane>
          <TabPane tab="Control de Inasistencias" key="2">
            <div style={{ marginBottom: '16px', textAlign: 'right' }}>
              <Button type="primary" danger icon={<FrownOutlined />} onClick={() => setIsInaModalVisible(true)}>Registrar Falta</Button>
            </div>
            <Table 
              dataSource={inasistencias} 
              columns={columnsInasistencias} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* Modal Vacaciones */}
      <Modal title="Solicitar Vacaciones" visible={isVacModalVisible} onCancel={() => setIsVacModalVisible(false)} footer={null}>
        <Form form={formVac} layout="vertical" onFinish={handleRequestVacation}>
          <Form.Item name="empleado_id" label="Empleado" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="fechas" label="Periodo" rules={[{ required: true }]}>
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)' }}>Enviar Solicitud</Button>
        </Form>
      </Modal>

      {/* Modal Inasistencias */}
      <Modal title="Registrar Inasistencia" visible={isInaModalVisible} onCancel={() => setIsInaModalVisible(false)} footer={null}>
        <Form form={formIna} layout="vertical" onFinish={handleRegisterInasistencia}>
          <Form.Item name="empleado_id" label="Empleado" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="fecha" label="Fecha de la falta" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="motivo" label="Motivo (Opcional)">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="justificada" label="¿Está Justificada?" initialValue="false">
            <Select>
              <Option value="false">No (Descuenta Día)</Option>
              <Option value="true">Sí (No descuenta Día)</Option>
            </Select>
          </Form.Item>
          <Button type="primary" danger htmlType="submit" block>Registrar Falta</Button>
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
