import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Typography, Tag, InputNumber } from 'antd';
import { PlusOutlined, CheckOutlined } from '@ant-design/icons';
import { productionService, OrdenProduccion } from '../../services/productionService';
import { inventoryService, Producto } from '../../services/inventoryService';

const { Title } = Typography;

const ProductionOrders: React.FC = () => {
  const [ordenes, setOrdenes] = useState<OrdenProduccion[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isCreateVisible, setIsCreateVisible] = useState(false);
  const [isFinishVisible, setIsFinishVisible] = useState(false);
  const [selectedOrden, setSelectedOrden] = useState<OrdenProduccion | null>(null);
  
  const [createForm] = Form.useForm();
  const [finishForm] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [ords, prods] = await Promise.all([
        productionService.getOrdenes(),
        inventoryService.getProductos()
      ]);
      setOrdenes(ords);
      setProductos(prods);
    } catch (error) {
      message.error("Error al cargar datos.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      const payload = {
        ...values,
        folio: `OP-${Math.floor(Math.random() * 10000)}`
      };
      await productionService.createOrden(payload);
      message.success("Orden de producción creada.");
      setIsCreateVisible(false);
      createForm.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al crear la orden");
    }
  };

  const handleFinish = async (values: any) => {
    if (!selectedOrden) return;
    try {
      await productionService.finalizarOrden(selectedOrden.id, values);
      message.success("Orden completada. Inventario actualizado y póliza generada.");
      setIsFinishVisible(false);
      finishForm.resetFields();
      setSelectedOrden(null);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Error al finalizar la orden");
    }
  };

  const columns = [
    { title: 'Folio', dataIndex: 'folio', key: 'folio' },
    { 
      title: 'Producto Final', 
      key: 'producto',
      render: (_: any, record: OrdenProduccion) => {
        const prod = productos.find(p => p.id === record.producto_final_id);
        return prod ? prod.nombre : record.producto_final_id;
      }
    },
    { title: 'Prog.', dataIndex: 'cantidad_programada', key: 'prog' },
    { title: 'Prod.', dataIndex: 'cantidad_producida', key: 'prod' },
    { 
      title: 'Estado', 
      key: 'estado',
      render: (_: any, record: OrdenProduccion) => {
        let color = 'gold';
        if (record.estado === 'completado') color = 'green';
        if (record.estado === 'en_proceso') color = 'blue';
        return <Tag color={color}>{record.estado.toUpperCase()}</Tag>;
      }
    },
    { 
      title: 'Acción', 
      key: 'accion',
      render: (_: any, record: OrdenProduccion) => (
        record.estado !== 'completado' && (
          <Button 
            type="primary" 
            size="small" 
            icon={<CheckOutlined />}
            onClick={() => {
              setSelectedOrden(record);
              finishForm.setFieldsValue({
                cantidad_real_producida: record.cantidad_programada,
                costo_maquila_adicional: 0
              });
              setIsFinishVisible(true);
            }}
          >
            Finalizar
          </Button>
        )
      )
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <Title level={3} style={{ color: 'var(--text-main)', margin: 0 }}>Órdenes de Producción</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsCreateVisible(true)} style={{ background: 'var(--accent-primary)' }}>
          Nueva Orden
        </Button>
      </div>

      <Table 
        dataSource={ordenes} 
        columns={columns} 
        rowKey="id" 
        loading={loading}
        className="dark-theme-table"
      />

      {/* MODAL CREAR ORDEN */}
      <Modal
        title="Lanzar Orden de Producción"
        open={isCreateVisible}
        onCancel={() => setIsCreateVisible(false)}
        onOk={() => createForm.submit()}
        destroyOnHidden
      >
        <Form form={createForm} onFinish={handleCreate} layout="vertical">
          <Form.Item name="producto_final_id" label="Modelo a Fabricar" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children">
              {productos.filter(p => p.tipo_producto === 'producto_terminado').map(c => 
                <Select.Option key={c.id} value={c.id}>{c.sku} - {c.nombre}</Select.Option>
              )}
            </Select>
          </Form.Item>
          <Form.Item name="cantidad_programada" label="Cantidad Programada" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
        </Form>
      </Modal>

      {/* MODAL FINALIZAR ORDEN */}
      <Modal
        title={`Finalizar Orden: ${selectedOrden?.folio}`}
        open={isFinishVisible}
        onCancel={() => setIsFinishVisible(false)}
        onOk={() => finishForm.submit()}
        destroyOnHidden
        okText="Completar y Generar Póliza"
      >
        <Form form={finishForm} onFinish={handleFinish} layout="vertical">
          <Form.Item name="cantidad_real_producida" label="Cantidad Real Producida" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          
          <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
            <Title level={5} style={{ color: 'var(--text-main)', marginTop: 0 }}>Costos de Maquila / Subcontratación</Title>
            <Form.Item name="maquilador_nombre" label="Nombre del Taller / Maquilero">
              <Input placeholder="Ej. Taller Doña Rosita (Opcional)" />
            </Form.Item>
            <Form.Item name="costo_maquila_adicional" label="Costo del Servicio ($)">
              <InputNumber style={{ width: '100%' }} min={0} precision={2} />
            </Form.Item>
            <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
              Al guardar, se descontarán las telas del almacén y se inyectarán las prendas terminadas al inventario. Además se generará la póliza de Diario de costo de manufactura.
            </Typography.Text>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default ProductionOrders;
