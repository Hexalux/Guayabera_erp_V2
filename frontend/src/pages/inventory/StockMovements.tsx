import React, { useEffect, useState } from 'react';
import { Card, Form, InputNumber, Select, Button, message, Alert, Typography, Divider, Spin } from 'antd';
import { SwapOutlined, InboxOutlined, SendOutlined } from '@ant-design/icons';
import { inventoryService, Producto, Almacen, Ubicacion, Lote } from '../../services/inventoryService';

const { Title, Text } = Typography;

const StockMovements: React.FC = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [almacenes, setAlmacenes] = useState<Almacen[]>([]);
  const [ubicaciones, setUbicaciones] = useState<Ubicacion[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [movTipo, setMovTipo] = useState<'entrada' | 'salida' | 'transferencia' | 'merma' | 'ajuste' | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [prods, alms, ubics, lts] = await Promise.all([
        inventoryService.getProductos(),
        inventoryService.getAlmacenes(),
        inventoryService.getUbicaciones(),
        inventoryService.getLotes()
      ]);
      setProductos(prods);
      setAlmacenes(alms);
      setUbicaciones(ubics);
      setLotes(lts);
    } catch (error) {
      message.error("Error al cargar datos del sistema");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUbicacionRapida = async () => {
    const nombre = prompt("Nombre del almacén rápido (Ej. Almacén Central):");
    if(nombre) {
      const alm = await inventoryService.createAlmacen({nombre, codigo: "ALM-"+Math.floor(Math.random()*1000)});
      await inventoryService.createUbicacion({almacen_id: alm.id, nombre: "Rack 1", pasillo: "1", rack: "1"});
      fetchData();
      message.success("Almacén y Rack creados.");
    }
  };

  const handleCreateLoteRapido = async () => {
    const pId = prompt("Pega el ID del Producto:");
    const num = prompt("Número de Lote:");
    if(pId && num) {
      await inventoryService.createLote({producto_id: pId, numero_lote: num, cantidad: 0});
      fetchData();
      message.success("Lote registrado.");
    }
  };

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      await inventoryService.registrarMovimiento({
        lote_id: values.lote_id,
        tipo_movimiento: values.tipo_movimiento,
        cantidad: values.cantidad,
        ubicacion_origen_id: values.tipo_movimiento !== 'entrada' ? values.ubicacion_origen_id : undefined,
        ubicacion_destino_id: values.tipo_movimiento !== 'salida' ? values.ubicacion_destino_id : undefined,
        referencia: values.referencia
      });
      message.success("Movimiento registrado y póliza contable automática generada con éxito");
      form.resetFields();
      setMovTipo(null);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Error al procesar movimiento");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={3} style={{ color: 'var(--text-main)', textAlign: 'center' }}>Terminal de Almacén</Title>
      
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
        <Button onClick={handleCreateUbicacionRapida}>Crear Almacén Rápido</Button>
        <Button onClick={handleCreateLoteRapido}>Crear Lote Rápido</Button>
      </div>

      <Spin spinning={loading}>
        <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)', borderRadius: '12px' }}>
          
          <Alert 
            message="Integración Contable Automática" 
            description="Las Entradas y Salidas ejecutarán pólizas automáticas de cargo y abono al costo usando tu catálogo SAT. Las Transferencias solo afectarán la ubicación física."
            type="info" 
            showIcon 
            style={{ marginBottom: '24px' }}
          />

          <Form layout="vertical" form={form} onFinish={onFinish}>
            
            <Form.Item name="tipo_movimiento" label="Tipo de Movimiento" rules={[{ required: true }]}>
              <Select onChange={setMovTipo} placeholder="Selecciona la operación">
                <Select.Option value="entrada"><InboxOutlined /> Entrada de Ajuste / Compra</Select.Option>
                <Select.Option value="salida"><SendOutlined /> Salida / Costo de Ventas</Select.Option>
                <Select.Option value="transferencia"><SwapOutlined /> Transferencia Interna</Select.Option>
                <Select.Option value="merma"><SendOutlined /> Merma / Producto Dañado</Select.Option>
                <Select.Option value="ajuste"><SwapOutlined /> Ajuste Manual de Inventario</Select.Option>
              </Select>
            </Form.Item>

            <Divider style={{ borderColor: 'var(--text-secondary)' }} />

            <Form.Item name="lote_id" label="Lote del Producto" rules={[{ required: true }]}>
              <Select showSearch optionFilterProp="children" placeholder="Busca por lote o producto">
                {lotes.map(l => {
                  const p = productos.find(x => x.id === l.producto_id);
                  return (
                    <Select.Option key={l.id} value={l.id}>
                      {p?.nombre} - Lote: {l.numero_lote} (Stock actual: {l.cantidad})
                    </Select.Option>
                  )
                })}
              </Select>
            </Form.Item>

            <Form.Item name="cantidad" label="Cantidad" rules={[{ required: true, type: 'number', min: 0.01 }]}>
              <InputNumber style={{ width: '100%' }} precision={2} />
            </Form.Item>

            { (movTipo === 'salida' || movTipo === 'transferencia' || movTipo === 'merma') && (
              <Form.Item name="ubicacion_origen_id" label="Ubicación de Origen" rules={[{ required: true }]}>
                <Select>
                  {ubicaciones.map(u => <Select.Option key={u.id} value={u.id}>{u.nombre}</Select.Option>)}
                </Select>
              </Form.Item>
            )}

            { (movTipo === 'entrada' || movTipo === 'transferencia') && (
              <Form.Item name="ubicacion_destino_id" label="Ubicación de Destino" rules={[{ required: true }]}>
                <Select>
                  {ubicaciones.map(u => <Select.Option key={u.id} value={u.id}>{u.nombre}</Select.Option>)}
                </Select>
              </Form.Item>
            )}

            <Button type="primary" htmlType="submit" block size="large" style={{ background: 'var(--accent-primary)', marginTop: '16px' }}>
              Ejecutar Transacción Segura
            </Button>
          </Form>

        </Card>
      </Spin>
    </div>
  );
};

export default StockMovements;
