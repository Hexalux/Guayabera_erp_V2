import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography } from 'antd';
import { RocketOutlined, ScissorOutlined, CheckCircleOutlined, DollarOutlined } from '@ant-design/icons';
import { productionService, OrdenProduccion } from '../../services/productionService';

const { Title } = Typography;

const ProductionDashboard: React.FC = () => {
  const [ordenes, setOrdenes] = useState<OrdenProduccion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await productionService.getOrdenes();
      setOrdenes(data);
    } catch (error) {
      console.error("Error fetching production stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const enProceso = ordenes.filter(o => o.estado !== 'completado').length;
  const completadas = ordenes.filter(o => o.estado === 'completado').length;
  const costoTotal = ordenes.reduce((acc, o) => acc + (o.costo_total || 0), 0);
  const prendasProducidas = ordenes.reduce((acc, o) => acc + (o.cantidad_producida || 0), 0);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ color: 'var(--text-main)', marginBottom: '24px' }}>
        Fábrica & Producción
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Órdenes Activas</span>}
              value={enProceso}
              prefix={<RocketOutlined style={{ color: '#F44336' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Órdenes Completadas</span>}
              value={completadas}
              prefix={<CheckCircleOutlined style={{ color: 'var(--accent-primary)' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Prendas Fabricadas</span>}
              value={prendasProducidas}
              prefix={<ScissorOutlined style={{ color: 'var(--accent-secondary)' }} />}
              valueStyle={{ color: 'var(--text-main)' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ background: 'var(--bg-secondary)', borderColor: 'var(--bg-secondary)' }}>
            <Statistic
              title={<span style={{ color: 'var(--text-secondary)' }}>Costo Total Invertido</span>}
              value={costoTotal}
              prefix={<DollarOutlined style={{ color: '#2196F3' }} />}
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

export default ProductionDashboard;
