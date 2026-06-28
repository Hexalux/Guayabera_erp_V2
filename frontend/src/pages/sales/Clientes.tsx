import React, { useState, useEffect } from 'react';
import { Table, Button, Typography, Modal, Form, Input, InputNumber, Space, Card, message } from 'antd';
import { PlusOutlined, UserAddOutlined, SolutionOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';

const { Title, Text } = Typography;

export const Clientes: React.FC = () => {
    const [clientes, setClientes] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [form] = Form.useForm();

    const fetchClientes = async () => {
        setLoading(true);
        try {
            const res = await api.get('/sales/clientes');
            setClientes(res.data);
        } catch (error) {
            console.error(error);
            message.error('Error al cargar los clientes.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchClientes();
    }, []);

    const handleCreateCliente = async (values: any) => {
        try {
            await api.post('/sales/clientes', values);
            message.success('Cliente registrado exitosamente.');
            setIsModalVisible(false);
            form.resetFields();
            fetchClientes();
        } catch (error) {
            console.error(error);
            message.error('No se pudo registrar el cliente.');
        }
    };

    const columns = [
        { 
            title: 'Razón Social / Nombre', 
            dataIndex: 'razon_social', 
            key: 'razon_social',
            render: (text: string) => <Text style={{ color: '#FFF', fontWeight: 'bold' }}>{text}</Text>
        },
        { 
            title: 'RFC', 
            dataIndex: 'rfc', 
            key: 'rfc',
            render: (text: string) => <Text style={{ color: '#DAA520' }}>{text || 'PÚBLICO EN GENERAL'}</Text>
        },
        { 
            title: 'Email', 
            dataIndex: 'email', 
            key: 'email',
            render: (text: string) => <span style={{ color: '#B8B9BD' }}>{text || '-'}</span>
        },
        { 
            title: 'Teléfono', 
            dataIndex: 'telefono', 
            key: 'telefono',
            render: (text: string) => <span style={{ color: '#B8B9BD' }}>{text || '-'}</span>
        },
        { 
            title: 'Límite de Crédito', 
            dataIndex: 'limite_credito', 
            key: 'limite_credito', 
            render: (val: number) => <Text style={{ color: '#00A651', fontWeight: 'bold' }}>${(val || 0).toFixed(2)}</Text> 
        },
    ];

    return (
        <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF', textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <Title level={2} style={{ color: '#00A651', margin: 0 }}>Catálogo de Clientes</Title>
                <Button 
                    type="primary" 
                    icon={<UserAddOutlined />} 
                    onClick={() => setIsModalVisible(true)}
                    style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
                >
                    Registrar Cliente
                </Button>
            </div>

            <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bordered={false}>
                <Table 
                    columns={columns} 
                    dataSource={clientes} 
                    rowKey="id" 
                    loading={loading}
                    className="dark-table" 
                />
            </Card>

            <Modal
                title={<span style={{ color: '#DAA520' }}><SolutionOutlined /> Registrar Nuevo Cliente</span>}
                open={isModalVisible}
                onOk={() => form.submit()}
                onCancel={() => setIsModalVisible(false)}
                okText="Guardar"
                cancelText="Cancelar"
                bodyStyle={{ backgroundColor: '#161A24', padding: '16px 0' }}
                className="dark-modal"
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreateCliente}
                >
                    <Form.Item 
                        name="razon_social" 
                        label={<span style={{ color: '#FFF' }}>Razón Social / Nombre Completo</span>}
                        rules={[{ required: true, message: 'La razón social es obligatoria.' }]}
                    >
                        <Input placeholder="Ej. Distribuidora de Guayaberas del Sureste" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>

                    <Form.Item 
                        name="rfc" 
                        label={<span style={{ color: '#FFF' }}>RFC</span>}
                    >
                        <Input placeholder="Ej. XAXX010101000" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>

                    <Form.Item 
                        name="email" 
                        label={<span style={{ color: '#FFF' }}>Correo Electrónico</span>}
                        rules={[{ type: 'email', message: 'Ingresa un correo electrónico válido.' }]}
                    >
                        <Input placeholder="ejemplo@correo.com" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>

                    <Form.Item 
                        name="telefono" 
                        label={<span style={{ color: '#FFF' }}>Teléfono de Contacto</span>}
                    >
                        <Input placeholder="Ej. 9991234567" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>

                    <Form.Item 
                        name="direccion" 
                        label={<span style={{ color: '#FFF' }}>Dirección Fiscal / Entrega</span>}
                    >
                        <Input.TextArea placeholder="Calle 60 #100 x 21 y 23, Mérida, Yucatán" style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
                    </Form.Item>

                    <Form.Item 
                        name="limite_credito" 
                        label={<span style={{ color: '#FFF' }}>Límite de Crédito Autorizado ($)</span>}
                        initialValue={0}
                    >
                        <InputNumber min={0} style={{ width: '100%', backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }} />
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
