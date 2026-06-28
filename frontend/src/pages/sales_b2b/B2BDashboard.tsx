import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Table, Typography, Space, Tag, Modal, Form, Select, DatePicker, message, InputNumber, Input } from 'antd';
import { ShoppingCartOutlined, FileTextOutlined, SyncOutlined, SendOutlined, CheckCircleOutlined, CarOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface Cotizacion {
  id: string;
  folio: string;
  cliente_nombre: string;
  fecha_vigencia: string;
  total: number;
  estado: string;
}

interface Pedido {
  id: string;
  folio: string;
  cliente_nombre: string;
  fecha_entrega_esperada: string;
  total: number;
  estado: string;
}

interface Producto {
  id: string;
  nombre: string;
  precio_venta: number;
}

interface Cliente {
  id: string;
  nombre_comercial: string;
}

export const B2BDashboard: React.FC = () => {
  const [cotizaciones, setCotizaciones] = useState<Cotizacion[]>([]);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(false);
  
  const [isCotModalVisible, setIsCotModalVisible] = useState(false);
  const [formCot] = Form.useForm();
  
  // Para manejar lineas de detalle dinámicas
  const [detallesCot, setDetallesCot] = useState<any[]>([{ id: Date.now(), producto_textil_id: '', cantidad: 1, precio_unitario: 0 }]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resCot, resPed, resProd, resCli] = await Promise.all([
        api.get('/sales-b2b/cotizaciones'),
        api.get('/sales-b2b/pedidos'),
        api.get('/inventory/products'),
        api.get('/sales/clientes')
      ]);
      setCotizaciones(resCot.data);
      setPedidos(resPed.data);
      setProductos(resProd.data);
      setClientes(resCli.data);
    } catch (error) {
      message.error('Error al cargar datos B2B');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCotizacion = async (values: any) => {
    try {
      const payload = {
        cliente_id: values.cliente_id,
        fecha_vigencia: values.fecha_vigencia.toISOString(),
        notas: values.notas,
        detalles: detallesCot.filter(d => d.producto_textil_id).map(d => ({
          producto_textil_id: d.producto_textil_id,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario
        }))
      };
      
      await api.post('/sales-b2b/cotizaciones', payload);
      message.success('Cotización creada exitosamente');
      setIsCotModalVisible(false);
      formCot.resetFields();
      setDetallesCot([{ id: Date.now(), producto_textil_id: '', cantidad: 1, precio_unitario: 0 }]);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al crear cotización');
    }
  };

  const handleConvertirPedido = async (id: string) => {
    try {
      await api.post(`/sales-b2b/cotizaciones/${id}/convertir-pedido`);
      message.success('Cotización convertida a Pedido correctamente');
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al convertir pedido');
    }
  };

  const handleRemisionar = async (id: string) => {
    try {
      await api.post(`/sales-b2b/pedidos/${id}/remisionar`);
      message.success('Pedido remisionado, inventario descontado y póliza generada');
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al remisionar');
    }
  };

  const cotColumns = [
    { title: 'Folio', dataIndex: 'folio', key: 'folio', render: (t: string) => <Tag color="blue">{t}</Tag> },
    { title: 'Cliente', dataIndex: 'cliente_nombre', key: 'cliente', render: (t: string) => <Text strong style={{ color: '#FFF' }}>{t}</Text> },
    { title: 'Total', dataIndex: 'total', key: 'total', render: (v: number) => <Text style={{ color: '#00A651' }}>${v.toFixed(2)}</Text> },
    { 
      title: 'Estado', dataIndex: 'estado', key: 'estado', 
      render: (t: string) => <Tag color={t === 'aceptada' ? 'success' : 'default'}>{t.toUpperCase()}</Tag> 
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Cotizacion) => (
        record.estado !== 'aceptada' && (
          <Button 
            size="small" 
            type="primary" 
            style={{ backgroundColor: '#2196F3' }}
            icon={<CheckCircleOutlined />}
            onClick={() => handleConvertirPedido(record.id)}
          >
            Aprobar como Pedido
          </Button>
        )
      )
    }
  ];

  const pedColumns = [
    { title: 'Folio', dataIndex: 'folio', key: 'folio', render: (t: string) => <Tag color="purple">{t}</Tag> },
    { title: 'Cliente', dataIndex: 'cliente_nombre', key: 'cliente', render: (t: string) => <Text strong style={{ color: '#FFF' }}>{t}</Text> },
    { title: 'Total', dataIndex: 'total', key: 'total', render: (v: number) => <Text style={{ color: '#DAA520' }}>${v.toFixed(2)}</Text> },
    { 
      title: 'Estado', dataIndex: 'estado', key: 'estado', 
      render: (t: string) => <Tag color={t === 'remisionado_total' ? 'success' : 'processing'}>{t.toUpperCase()}</Tag> 
    },
    {
      title: 'Logística',
      key: 'acciones',
      render: (_: any, record: Pedido) => (
        record.estado !== 'remisionado_total' && (
          <Button 
            size="small" 
            style={{ backgroundColor: '#F44336', color: '#FFF', borderColor: '#F44336' }}
            icon={<CarOutlined />}
            onClick={() => handleRemisionar(record.id)}
          >
            Surtir y Remisionar
          </Button>
        )
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: '#2196F3', margin: 0 }}>
            <ShoppingCartOutlined /> Cadena de Suministro B2B
          </Title>
          <Text style={{ color: '#B8B9BD' }}>Gestión de Ventas Institucionales y Embudo Comercial</Text>
        </Col>
        <Col>
          <Space>
            <Button icon={<SyncOutlined />} onClick={fetchData} loading={loading}>
              Actualizar
            </Button>
            <Button 
              type="primary" 
              icon={<FileTextOutlined />} 
              onClick={() => setIsCotModalVisible(true)}
              style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
            >
              Nueva Cotización
            </Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card 
            title={<Text style={{ color: '#FFF' }}><FileTextOutlined /> Cotizaciones Abiertas</Text>}
            style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
            bodyStyle={{ padding: 0 }}
          >
            <Table 
              dataSource={cotizaciones} 
              columns={cotColumns} 
              rowKey="id"
              pagination={{ pageSize: 5 }}
              className="dark-table"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card 
            title={<Text style={{ color: '#FFF' }}><SendOutlined /> Pedidos en Firme (Por Surtir)</Text>}
            style={{ backgroundColor: '#161A24', borderColor: '#303030' }}
            bodyStyle={{ padding: 0 }}
          >
            <Table 
              dataSource={pedidos} 
              columns={pedColumns} 
              rowKey="id"
              pagination={{ pageSize: 5 }}
              className="dark-table"
            />
          </Card>
        </Col>
      </Row>

      {/* Modal Nueva Cotización */}
      <Modal
        title="Crear Cotización Comercial"
        open={isCotModalVisible}
        onOk={() => formCot.submit()}
        onCancel={() => setIsCotModalVisible(false)}
        width={800}
        okText="Guardar Cotización"
        cancelText="Cancelar"
      >
        <Form form={formCot} layout="vertical" onFinish={handleCreateCotizacion}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="cliente_id" label="Cliente B2B" rules={[{ required: true }]}>
                <Select placeholder="Seleccione el cliente">
                  {clientes.map(c => <Option key={c.id} value={c.id}>{c.nombre_comercial}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="fecha_vigencia" label="Válida hasta" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Text strong>Productos a Cotizar</Text>
          <div style={{ marginTop: '10px', marginBottom: '16px' }}>
            {detallesCot.map((det, index) => (
              <Row gutter={8} key={det.id} style={{ marginBottom: 8 }}>
                <Col span={12}>
                  <Select 
                    showSearch
                    placeholder="Producto" 
                    value={det.producto_textil_id}
                    onChange={val => {
                      const prod = productos.find(p => p.id === val);
                      const newDets = [...detallesCot];
                      newDets[index] = { ...newDets[index], producto_textil_id: val, precio_unitario: prod?.precio_venta || 0 };
                      setDetallesCot(newDets);
                    }}
                    style={{ width: '100%' }}
                  >
                    {productos.map(p => <Option key={p.id} value={p.id}>{p.nombre} (${p.precio_venta})</Option>)}
                  </Select>
                </Col>
                <Col span={6}>
                  <InputNumber 
                    min={1} 
                    value={det.cantidad} 
                    onChange={val => {
                      const newDets = [...detallesCot];
                      newDets[index].cantidad = val || 1;
                      setDetallesCot(newDets);
                    }}
                    style={{ width: '100%' }} 
                    placeholder="Cant."
                  />
                </Col>
                <Col span={6}>
                  <InputNumber 
                    min={0} 
                    value={det.precio_unitario} 
                    onChange={val => {
                      const newDets = [...detallesCot];
                      newDets[index].precio_unitario = val || 0;
                      setDetallesCot(newDets);
                    }}
                    style={{ width: '100%' }} 
                    placeholder="Precio"
                  />
                </Col>
              </Row>
            ))}
            <Button 
              type="dashed" 
              onClick={() => setDetallesCot([...detallesCot, { id: Date.now(), producto_textil_id: '', cantidad: 1, precio_unitario: 0 }])}
              block
            >
              + Agregar Partida
            </Button>
          </div>

          <Form.Item name="notas" label="Notas Adicionales">
            <Input.TextArea rows={2} placeholder="Condiciones comerciales especiales..." />
          </Form.Item>
        </Form>
      </Modal>

      <style>{`
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
      `}</style>
    </div>
  );
};
