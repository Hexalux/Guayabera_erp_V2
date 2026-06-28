import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Typography, Modal, Form, Input, InputNumber, Space, message, Tabs } from 'antd';
import { PlusOutlined, UnorderedListOutlined } from '@ant-design/icons';
import { purchasesService, Proveedor, ListaPrecioProveedor } from '../../services/purchasesService';
import { inventoryService, Producto } from '../../services/inventoryService';

const { Title } = Typography;
const { TabPane } = Tabs;

export const Proveedores: React.FC = () => {
    const [proveedores, setProveedores] = useState<Proveedor[]>([]);
    const [productos, setProductos] = useState<Producto[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Modals state
    const [isProvModalOpen, setIsProvModalOpen] = useState(false);
    const [isPrecioModalOpen, setIsPrecioModalOpen] = useState(false);
    
    const [provForm] = Form.useForm();
    const [precioForm] = Form.useForm();
    
    const [selectedProveedor, setSelectedProveedor] = useState<Proveedor | null>(null);
    const [preciosList, setPreciosList] = useState<ListaPrecioProveedor[]>([]);
    const [loadingPrecios, setLoadingPrecios] = useState(false);

    useEffect(() => {
        fetchProveedores();
        fetchProductos();
    }, []);

    const fetchProveedores = async () => {
        setLoading(true);
        try {
            const data = await purchasesService.getProveedores();
            setProveedores(data);
        } catch (error) {
            message.error('Error al cargar proveedores');
        } finally {
            setLoading(false);
        }
    };

    const fetchProductos = async () => {
        try {
            const data = await inventoryService.getProductos();
            setProductos(data);
        } catch (error) {
            message.error('Error al cargar productos');
        }
    };

    const fetchPrecios = async (proveedorId: string) => {
        setLoadingPrecios(true);
        try {
            const data = await purchasesService.getPreciosProveedor(proveedorId);
            setPreciosList(data);
        } catch (error) {
            message.error('Error al cargar listas de precio');
        } finally {
            setLoadingPrecios(false);
        }
    };

    const handleCreateProveedor = async (values: any) => {
        try {
            await purchasesService.createProveedor(values);
            message.success('Proveedor creado con éxito');
            setIsProvModalOpen(false);
            provForm.resetFields();
            fetchProveedores();
        } catch (error) {
            message.error('Error al crear proveedor');
        }
    };

    const handleCreatePrecio = async (values: any) => {
        if (!selectedProveedor) return;
        try {
            await purchasesService.createPrecioProveedor(selectedProveedor.id, values);
            message.success('Precio agregado con éxito');
            setIsPrecioModalOpen(false);
            precioForm.resetFields();
            fetchPrecios(selectedProveedor.id);
        } catch (error) {
            message.error('Error al agregar precio');
        }
    };

    const openPrecios = (prov: Proveedor) => {
        setSelectedProveedor(prov);
        fetchPrecios(prov.id);
    };

    const columns = [
        { title: 'Razón Social', dataIndex: 'razon_social', key: 'razon_social' },
        { title: 'RFC', dataIndex: 'rfc', key: 'rfc' },
        { title: 'Email', dataIndex: 'email', key: 'email' },
        { title: 'Teléfono', dataIndex: 'telefono', key: 'telefono' },
        { title: 'Días Crédito', dataIndex: 'dias_credito', key: 'dias_credito' },
        {
            title: 'Acciones',
            key: 'acciones',
            render: (_: any, record: Proveedor) => (
                <Button 
                    type="link" 
                    icon={<UnorderedListOutlined />}
                    onClick={() => openPrecios(record)}
                >
                    Listas de Precio
                </Button>
            )
        }
    ];

    const preciosCols = [
        { 
            title: 'Producto', 
            dataIndex: 'producto_textil_id', 
            key: 'producto',
            render: (id: string) => productos.find(p => p.id === id)?.nombre || id
        },
        { title: 'Código Proveedor', dataIndex: 'codigo_proveedor', key: 'codigo_proveedor' },
        { title: 'Precio', dataIndex: 'precio', key: 'precio', render: (val: number) => `$${val.toFixed(2)}` },
        { title: 'Moneda', dataIndex: 'moneda', key: 'moneda' },
        { title: 'Factor Conversión', dataIndex: 'factor_conversion', key: 'factor_conversion' },
    ];

    return (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <Title level={4} style={{ margin: 0 }}>Proveedores</Title>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsProvModalOpen(true)}>
                        Nuevo Proveedor
                    </Button>
                </div>
                <Table 
                    dataSource={proveedores} 
                    columns={columns} 
                    rowKey="id" 
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {selectedProveedor && (
                <Card title={`Listas de Precio: ${selectedProveedor.razon_social}`}>
                    <div style={{ marginBottom: 16 }}>
                        <Button type="dashed" icon={<PlusOutlined />} onClick={() => setIsPrecioModalOpen(true)}>
                            Agregar Precio
                        </Button>
                    </div>
                    <Table 
                        dataSource={preciosList} 
                        columns={preciosCols} 
                        rowKey="id" 
                        loading={loadingPrecios}
                        pagination={false}
                    />
                </Card>
            )}

            <Modal
                title="Nuevo Proveedor"
                open={isProvModalOpen}
                onCancel={() => setIsProvModalOpen(false)}
                onOk={() => provForm.submit()}
            >
                <Form form={provForm} layout="vertical" onFinish={handleCreateProveedor}>
                    <Form.Item name="razon_social" label="Razón Social" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="rfc" label="RFC">
                        <Input />
                    </Form.Item>
                    <Form.Item name="email" label="Email">
                        <Input type="email" />
                    </Form.Item>
                    <Form.Item name="telefono" label="Teléfono">
                        <Input />
                    </Form.Item>
                    <Form.Item name="dias_credito" label="Días de Crédito" initialValue={0}>
                        <InputNumber min={0} style={{ width: '100%' }} />
                    </Form.Item>
                </Form>
            </Modal>

            <Modal
                title={`Nuevo Precio para ${selectedProveedor?.razon_social}`}
                open={isPrecioModalOpen}
                onCancel={() => setIsPrecioModalOpen(false)}
                onOk={() => precioForm.submit()}
            >
                <Form form={precioForm} layout="vertical" onFinish={handleCreatePrecio}>
                    <Form.Item name="producto_textil_id" label="Producto Interno" rules={[{ required: true }]}>
                        <select className="ant-input" style={{ width: '100%' }}>
                            <option value="">Seleccione...</option>
                            {productos.map(p => (
                                <option key={p.id} value={p.id}>{p.nombre} ({p.sku})</option>
                            ))}
                        </select>
                    </Form.Item>
                    <Form.Item name="codigo_proveedor" label="Código del Proveedor">
                        <Input />
                    </Form.Item>
                    <Form.Item name="precio" label="Precio Unitario" rules={[{ required: true }]}>
                        <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="moneda" label="Moneda" initialValue="MXN">
                        <Input />
                    </Form.Item>
                    <Form.Item name="factor_conversion" label="Factor de Conversión (Ej: 1 rollo = 50 mts)" initialValue={1.0}>
                        <InputNumber min={0.01} step={0.01} style={{ width: '100%' }} />
                    </Form.Item>
                </Form>
            </Modal>
        </Space>
    );
};
