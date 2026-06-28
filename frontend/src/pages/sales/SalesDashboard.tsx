import React from 'react';
import { Typography, Card, Row, Col, Statistic } from 'antd';
import { DollarOutlined, ShoppingCartOutlined, TeamOutlined } from '@ant-design/icons';

const { Title } = Typography;

export const SalesDashboard: React.FC = () => {
    return (
        <div>
            <Title level={2}>Dashboard de Ventas</Title>
            <Row gutter={16}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Ventas del Mes" value={112893} prefix={<DollarOutlined />} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Órdenes Pendientes" value={14} prefix={<ShoppingCartOutlined />} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Nuevos Clientes" value={9} prefix={<TeamOutlined />} />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
