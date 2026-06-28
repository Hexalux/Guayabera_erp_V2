import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Typography, Modal, Form, Input, Space, message, Tabs, Checkbox } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { inventoryService, Categoria, UnidadMedida } from '../../services/inventoryService';

const { Title } = Typography;
const { TabPane } = Tabs;

export const ConfiguracionInventario: React.FC = () => {
    const [activeTab, setActiveTab] = useState('categorias');
    
    // Data states
    const [categorias, setCategorias] = useState<Categoria[]>([]);
    const [unidades, setUnidades] = useState<UnidadMedida[]>([]);
    const [loading, setLoading] = useState(false);

    // Modal states
    const [isCatModalOpen, setIsCatModalOpen] = useState(false);
    const [isUmModalOpen, setIsUmModalOpen] = useState(false);

    const [catForm] = Form.useForm();
    const [umForm] = Form.useForm();

    useEffect(() => {
        if (activeTab === 'categorias') {
            fetchCategorias();
        } else if (activeTab === 'unidades') {
            fetchUnidades();
        }
    }, [activeTab]);

    const fetchCategorias = async () => {
        setLoading(true);
        try {
            const data = await inventoryService.getCategorias();
            setCategorias(data);
        } catch (error) {
            message.error('Error al cargar categorías');
        } finally {
            setLoading(false);
        }
    };

    const fetchUnidades = async () => {
        setLoading(true);
        try {
            const data = await inventoryService.getUnidadesMedida();
            setUnidades(data);
        } catch (error) {
            message.error('Error al cargar unidades de medida');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateCategoria = async (values: any) => {
        try {
            await inventoryService.createCategoria(values);
            message.success('Categoría creada');
            setIsCatModalOpen(false);
            catForm.resetFields();
            fetchCategorias();
        } catch (error) {
            message.error('Error al crear categoría');
        }
    };

    const handleCreateUnidad = async (values: any) => {
        try {
            await inventoryService.createUnidadMedida(values);
            message.success('Unidad de medida creada');
            setIsUmModalOpen(false);
            umForm.resetFields();
            fetchUnidades();
        } catch (error) {
            message.error('Error al crear unidad de medida');
        }
    };

    const catColumns = [
        { title: 'Código', dataIndex: 'codigo', key: 'codigo' },
        { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
        { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion' },
    ];

    const umColumns = [
        { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
        { title: 'Abreviatura', dataIndex: 'abreviatura', key: 'abreviatura' },
        { title: 'Activo', dataIndex: 'is_active', key: 'is_active', render: (val: boolean) => val ? 'Sí' : 'No' },
    ];

    return (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <Title level={4} style={{ margin: 0 }}>Configuración de Inventario</Title>
                    <Space>
                        {activeTab === 'categorias' && (
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsCatModalOpen(true)}>
                                Nueva Categoría
                            </Button>
                        )}
                        {activeTab === 'unidades' && (
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsUmModalOpen(true)}>
                                Nueva Unidad de Medida
                            </Button>
                        )}
                    </Space>
                </div>

                <Tabs activeKey={activeTab} onChange={setActiveTab}>
                    <TabPane tab="Categorías" key="categorias">
                        <Table 
                            dataSource={categorias} 
                            columns={catColumns} 
                            rowKey="id" 
                            loading={loading}
                            pagination={{ pageSize: 10 }}
                        />
                    </TabPane>
                    <TabPane tab="Unidades de Medida" key="unidades">
                        <Table 
                            dataSource={unidades} 
                            columns={umColumns} 
                            rowKey="id" 
                            loading={loading}
                            pagination={{ pageSize: 10 }}
                        />
                    </TabPane>
                </Tabs>
            </Card>

            <Modal
                title="Nueva Categoría"
                open={isCatModalOpen}
                onCancel={() => setIsCatModalOpen(false)}
                onOk={() => catForm.submit()}
            >
                <Form form={catForm} layout="vertical" onFinish={handleCreateCategoria}>
                    <Form.Item name="codigo" label="Código" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="nombre" label="Nombre" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="descripcion" label="Descripción">
                        <Input.TextArea />
                    </Form.Item>
                </Form>
            </Modal>

            <Modal
                title="Nueva Unidad de Medida"
                open={isUmModalOpen}
                onCancel={() => setIsUmModalOpen(false)}
                onOk={() => umForm.submit()}
            >
                <Form form={umForm} layout="vertical" onFinish={handleCreateUnidad}>
                    <Form.Item name="nombre" label="Nombre" rules={[{ required: true }]}>
                        <Input placeholder="Ej. Metros" />
                    </Form.Item>
                    <Form.Item name="abreviatura" label="Abreviatura" rules={[{ required: true }]}>
                        <Input placeholder="Ej. m" />
                    </Form.Item>
                    <Form.Item name="is_active" valuePropName="checked" initialValue={true}>
                        <Checkbox>Activo</Checkbox>
                    </Form.Item>
                </Form>
            </Modal>
        </Space>
    );
};
