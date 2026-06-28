import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography } from 'antd';
import { AppstoreOutlined, ShoppingCartOutlined, SwapOutlined, BarcodeOutlined } from '@ant-design/icons';
import { inventoryService, Producto, Lote } from '../../services/inventoryService';

const { Title } = Typography;

const InventoryDashboard: React.FC = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [prods, lts] = await Promise.all([
        inventoryService.getProductos(),
        inventoryService.getLotes()
      ]);
      setProductos(prods);
      setLotes(lts);
    } catch (error) {
      console.error("Error fetching inventory stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const totalUnidades = lotes.reduce((acc, lote) => acc + Number(lote.cantidad), 0);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ color: 'var(--text-main)', marginBottom: '24px' }}>
        Trazabilidad e Inventario
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Total Productos (SKUs)</span>}
              value={productos.length}
              prefix={<BarcodeOutlined style={{ color: 'var(--accent-primary)' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Unidades en Stock</span>}
              value={totalUnidades}
              prefix={<AppstoreOutlined style={{ color: 'var(--accent-secondary)' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Lotes Activos</span>}
              value={lotes.length}
              prefix={<SwapOutlined style={{ color: '#2196F3' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Valor Estimado</span>}
              value={totalUnidades * 100} // Placeholder de costo
              prefix={<ShoppingCartOutlined style={{ color: '#F44336' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
              formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default InventoryDashboard;
