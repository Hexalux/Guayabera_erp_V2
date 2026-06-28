import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { inventoryService, Producto, Categoria } from '../../services/inventoryService';

const { Title } = Typography;

const ProductsList: React.FC = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [prods, cats] = await Promise.all([
        inventoryService.getProductos(),
        inventoryService.getCategorias()
      ]);
      setProductos(prods);
      setCategorias(cats);
    } catch (error) {
      message.error("Error al cargar productos.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await inventoryService.createProducto(values);
      message.success("Producto creado con éxito");
      setIsModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error("Error al crear producto");
    }
  };

  const columns = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku' },
    { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
    { title: 'Tipo', dataIndex: 'tipo_producto', key: 'tipo' },
    { title: 'Composición', dataIndex: 'composicion', key: 'composicion' },
    { title: 'Color', dataIndex: 'color_pantone', key: 'color' },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <Title level={3} style={{ color: 'var(--text-main)', margin: 0 }}>Catálogo de Productos</Title>
        <Space>
          <Button onClick={() => {
            const catName = prompt("Nombre de categoría:");
            const catCode = prompt("Código de categoría:");
            if(catName && catCode) {
              inventoryService.createCategoria({nombre: catName, codigo: catCode}).then(fetchData);
            }
          }}>+ Categoría</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)} style={{ background: 'var(--accent-primary)' }}>
            Nuevo Producto
          </Button>
        </Space>
      </div>

      <Table 
        dataSource={productos} 
        columns={columns} 
        rowKey="id" 
        loading={loading}
        className="dark-theme-table"
      />

      <Modal
        title="Nuevo Producto Textil"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        destroyOnHidden
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="sku" label="SKU" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="nombre" label="Nombre del Producto" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="categoria_id" label="Categoría" rules={[{ required: true }]}>
            <Select>
              {categorias.map(c => <Select.Option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="tipo_producto" label="Tipo" initialValue="producto_terminado">
            <Select>
              <Select.Option value="tela">Tela</Select.Option>
              <Select.Option value="avio">Avío</Select.Option>
              <Select.Option value="producto_terminado">Producto Terminado</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="composicion" label="Composición (ej. 100% Lino)">
            <Input />
          </Form.Item>
          <Form.Item name="color_pantone" label="Color Pantone">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProductsList;
