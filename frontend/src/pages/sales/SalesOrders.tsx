import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Typography, Tag, Modal, Form, Select, Input, InputNumber, Card, message } from 'antd';
import { PlusOutlined, FileTextOutlined, CheckCircleOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;
const { Option } = Select;

export const SalesOrders: React.FC = () => {
    const [ordenes, setOrdenes] = useState<any[]>([]);
    const [clientes, setClientes] = useState<any[]>([]);
    const [productos, setProductos] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Modal Creación
    const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [selectedItems, setSelectedItems] = useState<any[]>([]);

    // Modal Detalle
    const [isDetailModalVisible, setIsDetailModalVisible] = useState(false);
    const [selectedOrder, setSelectedOrder] = useState<any>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [resOrdenes, resClientes, resProductos] = await Promise.all([
                api.get('/sales/ordenes'),
                api.get('/sales/clientes'),
                api.get('/inventory/productos')
            ]);
            setOrdenes(resOrdenes.data);
            setClientes(resClientes.data);
            setProductos(resProductos.data);
        } catch (error) {
            console.error(error);
            message.error('Error al cargar la información de ventas.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleConfirmOrder = async (id: string) => {
        try {
            await api.post(`/sales/ordenes/${id}/confirmar`);
            message.success('Orden confirmada exitosamente (Pólizas generadas).');
            fetchData();
        } catch (error: any) {
            console.error(error);
            message.error(error.response?.data?.detail || 'Error al confirmar la orden.');
        }
    };

    const handleCreateOrder = async (values: any) => {
        if (selectedItems.length === 0) {
            message.warning('Debes agregar al menos un producto a la cotización.');
            return;
        }

        try {
            const payload = {
                cliente_id: values.cliente_id,
                notas: values.notas,
                terminos_pago: values.terminos_pago,
                fecha_validez: values.fecha_validez,
                detalles: selectedItems.map(item => ({
                    producto_textil_id: item.producto_id,
                    cantidad: item.cantidad,
                    precio_unitario: item.precio_unitario,
                    descuento_porcentaje: item.descuento || 0
                }))
            };

            await api.post('/sales/ordenes', payload);
            message.success('Cotización creada exitosamente.');
            setIsCreateModalVisible(false);
            setSelectedItems([]);
            form.resetFields();
            fetchData();
        } catch (error: any) {
            console.error(error);
            message.error(error.response?.data?.detail || 'Error al crear la cotización.');
        }
    };

    const handleAddItem = (productId: string) => {
        const prod = productos.find(p => p.id === productId);
        if (!prod) return;

        const exists = selectedItems.find(item => item.producto_id === productId);
        if (exists) {
            message.warning('El producto ya está en la lista.');
            return;
        }

        // Precio base sugerido de MVP: $250.00
        setSelectedItems([
            ...selectedItems,
            {
                producto_id: prod.id,
                sku: prod.sku,
                nombre: prod.nombre,
                cantidad: 1,
                precio_unitario: 250.00,
                descuento: 0
            }
        ]);
    };

    const handleUpdateItem = (productId: string, key: string, val: number) => {
        const updated = selectedItems.map(item => {
            if (item.producto_id === productId) {
                return { ...item, [key]: val };
            }
            return item;
        });
        setSelectedItems(updated);
    };

    const handleRemoveItem = (productId: string) => {
        setSelectedItems(selectedItems.filter(item => item.producto_id !== productId));
    };

    const columns = [
        { 
            title: 'Folio', 
            dataIndex: 'folio', 
            key: 'folio',
            render: (text: string) => <Text style={{ color: '#FFF', fontWeight: 'bold' }}>{text}</Text>
        },
        { 
            title: 'Fecha Emisión', 
            dataIndex: 'fecha_emision', 
            key: 'fecha_emision', 
            render: (val: string) => new Date(val).toLocaleDateString() 
        },
        { 
            title: 'Estado', 
            dataIndex: 'estado', 
            key: 'estado', 
            render: (val: string) => (
                <Tag color={val === 'borrador' ? 'orange' : val === 'confirmada' ? 'green' : 'blue'}>
                    {val.toUpperCase()}
                </Tag>
            ) 
        },
        { 
            title: 'Total', 
            dataIndex: 'total', 
            key: 'total', 
            render: (val: number) => <Text style={{ color: '#00A651', fontWeight: 'bold' }}>${val.toFixed(2)}</Text> 
        },
        { 
            title: 'Acciones', 
            key: 'actions', 
            render: (_: any, record: any) => (
                <Space>
                    <Button 
                        size="small" 
                        icon={<InfoCircleOutlined />} 
                        onClick={() => {
                            setSelectedOrder(record);
                            setIsDetailModalVisible(true);
                        }}
                    >
                        Ver Detalle
                    </Button>
                    <Button 
                        size="small" 
                        type="primary" 
                        icon={<CheckCircleOutlined />}
                        disabled={record.estado !== 'borrador'} 
                        onClick={() => handleConfirmOrder(record.id)}
                        style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
                    >
                        Confirmar Pedido
                    </Button>
                </Space>
            )
        }
    ];

    const columnsItems = [
        { title: 'Producto', dataIndex: 'nombre', key: 'nombre', render: (text: string) => <span style={{ color: '#FFF' }}>{text}</span> },
        { 
            title: 'Cantidad', 
            key: 'cantidad', 
            render: (_: any, record: any) => (
                <InputNumber min={1} value={record.cantidad} onChange={v => handleUpdateItem(record.producto_id, 'cantidad', v || 1)} style={{ width: '80px', backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
            )
        },
        { 
            title: 'Precio U.', 
            key: 'precio', 
            render: (_: any, record: any) => (
                <InputNumber min={0} value={record.precio_unitario} onChange={v => handleUpdateItem(record.producto_id, 'precio_unitario', v || 0)} style={{ width: '120px', backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
            )
        },
        { 
            title: 'Descuento (%)', 
            key: 'descuento', 
            render: (_: any, record: any) => (
                <InputNumber min={0} max={100} value={record.descuento} onChange={v => handleUpdateItem(record.producto_id, 'descuento', v || 0)} style={{ width: '80px', backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
            )
        },
        {
            title: '',
            key: 'delete',
            render: (_: any, record: any) => (
                <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleRemoveItem(record.producto_id)} />
            )
        }
    ];

    return (
        <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF', textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <Title level={2} style={{ color: '#00A651', margin: 0 }}>Cotizaciones y Órdenes de Venta</Title>
                <Button 
                    type="primary" 
                    icon={<PlusOutlined />} 
                    onClick={() => setIsCreateModalVisible(true)}
                    style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
                >
                    Nueva Cotización
                </Button>
            </div>

            <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
                <Table 
                    columns={columns} 
                    dataSource={ordenes} 
                    rowKey="id" 
                    loading={loading}
                    className="dark-table" 
                />
            </Card>

            {/* Modal Creación */}
            <Modal
                title={<span style={{ color: '#DAA520' }}><FileTextOutlined /> Nueva Cotización</span>}
                open={isCreateModalVisible}
                onOk={() => form.submit()}
                onCancel={() => setIsCreateModalVisible(false)}
                okText="Crear Borrador"
                cancelText="Cancelar"
                width={800}
                bodyStyle={{ backgroundColor: '#161A24', padding: '16px 0' }}
                className="dark-modal"
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrder}>
                    <Space style={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
                        <Form.Item name="cliente_id" label={<span style={{ color: '#FFF' }}>Seleccionar Cliente</span>} rules={[{ required: true }]} style={{ width: '350px' }}>
                            <Select placeholder="Selecciona un cliente" dropdownStyle={{ backgroundColor: '#161A24' }}>
                                {clientes.map(c => (
                                    <Option key={c.id} value={c.id}>{c.razon_social}</Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item name="terminos_pago" label={<span style={{ color: '#FFF' }}>Términos de Pago</span>} style={{ width: '350px' }}>
                            <Select placeholder="Plazo de pago" dropdownStyle={{ backgroundColor: '#161A24' }}>
                                <Option value="CONTADO">Inmediato (Contado)</Option>
                                <Option value="15_DIAS">15 Días Crédito</Option>
                                <Option value="30_DIAS">30 Días Crédito</Option>
                            </Select>
                        </Form.Item>
                    </Space>

                    <div style={{ marginBottom: '24px' }}>
                        <span style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Buscar y Agregar Producto:</span>
                        <Select showSearch placeholder="Escribe el nombre del producto..." onChange={handleAddItem} style={{ width: '100%' }} filterOption={(input, option) => (option?.children as any).toLowerCase().includes(input.toLowerCase())}>
                            {productos.map(p => (
                                <Option key={p.id} value={p.id}>{p.nombre} ({p.sku})</Option>
                            ))}
                        </Select>
                    </div>

                    <Table 
                        dataSource={selectedItems}
                        columns={columnsItems}
                        rowKey="producto_id"
                        pagination={false}
                        size="small"
                        className="dark-table"
                        style={{ marginBottom: '24px' }}
                    />

                    <Form.Item name="notas" label={<span style={{ color: '#FFF' }}>Notas internas / Términos adicionales</span>}>
                        <Input.TextArea placeholder="Notas..." style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Modal Detalle */}
            <Modal
                title={<span style={{ color: '#DAA520' }}>Detalle de la Orden: {selectedOrder?.folio}</span>}
                open={isDetailModalVisible}
                onCancel={() => setIsDetailModalVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setIsDetailModalVisible(false)}>Cerrar</Button>
                ]}
                className="dark-modal"
            >
                {selectedOrder && (
                    <div>
                        <p><Text style={{ color: '#B8B9BD' }}>Estado: </Text><Tag color={selectedOrder.estado === 'borrador' ? 'orange' : 'green'}>{selectedOrder.estado.toUpperCase()}</Tag></p>
                        <p><Text style={{ color: '#B8B9BD' }}>Términos de Pago: </Text><Text style={{ color: '#FFF' }}>{selectedOrder.terminos_pago || 'No especificado'}</Text></p>
                        <p><Text style={{ color: '#B8B9BD' }}>Notas: </Text><Text style={{ color: '#FFF' }}>{selectedOrder.notas || '-'}</Text></p>
                        <p><Text style={{ color: '#B8B9BD' }}>Subtotal: </Text><Text style={{ color: '#FFF' }}>${selectedOrder.subtotal.toFixed(2)}</Text></p>
                        <p><Text style={{ color: '#B8B9BD' }}>IVA: </Text><Text style={{ color: '#FFF' }}>${selectedOrder.iva.toFixed(2)}</Text></p>
                        <p><Text style={{ color: '#B8B9BD' }}>Total: </Text><Text style={{ color: '#00A651', fontWeight: 'bold' }}>${selectedOrder.total.toFixed(2)}</Text></p>
                    </div>
                )}
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
                .ant-select-selector {
                    background-color: #0C0E14 !important;
                    color: #FFF !important;
                    border-color: #303030 !important;
                }
            `}</style>
        </div>
    );
};
