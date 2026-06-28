import React, { useState } from 'react';
import { Card, Input, Button, Timeline, Typography, Tag, Space, Divider, Row, Col, Statistic } from 'antd';
import { SearchOutlined, SafetyCertificateOutlined, CodeSandboxOutlined, NodeIndexOutlined, BankOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const TrazabilidadVisor: React.FC = () => {
  const [loteId, setLoteId] = useState('');
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = () => {
    if (!loteId) return;
    setLoading(true);
    // Simular búsqueda en el backend
    setTimeout(() => {
      setLoading(false);
      setSearched(true);
    }, 1500);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2} style={{ color: '#00A651' }}>Visor de Trazabilidad 360°</Title>
      <Text type="secondary">Consulta el ciclo de vida completo de un Lote de Producción, desde el insumo hasta la capitalización contable.</Text>

      <Card style={{ marginTop: '24px', backgroundColor: '#161A24', borderColor: '#DAA520', borderRadius: '12px' }} bordered>
        <Space.Compact style={{ width: '100%', maxWidth: '600px' }}>
          <Input 
            size="large" 
            placeholder="Ingrese Folio de Lote (ej. LOTE-PROD-ORD-001)" 
            value={loteId}
            onChange={e => setLoteId(e.target.value)}
            onPressEnter={handleSearch}
            prefix={<SearchOutlined style={{ color: '#DAA520' }} />}
            style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#DAA520' }}
          />
          <Button 
            size="large" 
            type="primary" 
            onClick={handleSearch} 
            loading={loading}
            style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
          >
            Rastrear Lote
          </Button>
        </Space.Compact>
      </Card>

      {searched && (
        <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
          <Col xs={24} lg={8}>
            <Card title={<span style={{ color: '#00A651' }}><SafetyCertificateOutlined /> Certificado de Autenticidad</span>} style={{ height: '100%', backgroundColor: '#161A24', borderColor: '#303030' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary">Lote:</Text>
                  <Title level={4} style={{ marginTop: 0, color: '#FFF' }}>{loteId}</Title>
                </div>
                <div>
                  <Text type="secondary">Producto:</Text>
                  <Text strong style={{ display: 'block', fontSize: '16px', color: '#FFF' }}>Guayabera Presidencial Lino Blanco (Talla M)</Text>
                </div>
                <div>
                  <Text type="secondary">Estado Actual:</Text>
                  <Tag color="success" style={{ display: 'block', width: 'fit-content', marginTop: '4px' }}>Capitalizado en Inventario PT</Tag>
                </div>
                <Divider style={{ borderColor: '#303030' }} />
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic title={<span style={{ color: '#B8B9BD' }}>Costo Unitario</span>} value={145.50} precision={2} prefix="$" valueStyle={{ color: '#DAA520' }} />
                  </Col>
                  <Col span={12}>
                    <Statistic title={<span style={{ color: '#B8B9BD' }}>Unidades</span>} value={50} valueStyle={{ color: '#FFF' }} />
                  </Col>
                </Row>
              </Space>
            </Card>
          </Col>
          
          <Col xs={24} lg={16}>
            <Card title={<span style={{ color: '#00A651' }}><NodeIndexOutlined /> Línea de Tiempo de Manufactura y Finanzas</span>} style={{ backgroundColor: '#161A24', borderColor: '#303030' }}>
              <Timeline
                mode="alternate"
                items={[
                  {
                    color: '#2196F3',
                    children: (
                      <>
                        <Text strong style={{ color: '#FFF' }}>Ingreso de Materia Prima</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>01 Junio 2026 09:00 AM</Text>
                        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#0C0E14', borderRadius: '4px' }}>
                          <Text style={{ color: '#B8B9BD' }}>Rollo Lino Blanco Italiano (Lote: RM-LINO-099)</Text>
                        </div>
                      </>
                    ),
                  },
                  {
                    color: '#DAA520',
                    dot: <CodeSandboxOutlined style={{ fontSize: '16px' }} />,
                    children: (
                      <>
                        <Text strong style={{ color: '#FFF' }}>Orden de Producción Iniciada</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>02 Junio 2026 11:30 AM</Text>
                        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#0C0E14', borderRadius: '4px' }}>
                          <Text style={{ color: '#B8B9BD' }}>Consumo de 125 Metros de Lino. Operador: Juan Pérez.</Text>
                        </div>
                      </>
                    ),
                  },
                  {
                    color: '#00A651',
                    children: (
                      <>
                        <Text strong style={{ color: '#FFF' }}>Cierre de Producción (ACID Tx)</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>04 Junio 2026 16:45 PM</Text>
                        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#0C0E14', borderRadius: '4px' }}>
                          <Text style={{ color: '#B8B9BD' }}>50 Unidades confeccionadas. Asignación Lote: {loteId}</Text>
                        </div>
                      </>
                    ),
                  },
                  {
                    color: '#DAA520',
                    dot: <BankOutlined style={{ fontSize: '16px' }} />,
                    children: (
                      <>
                        <Text strong style={{ color: '#FFF' }}>Capitalización Contable (Libro Mayor)</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>04 Junio 2026 16:45 PM</Text>
                        <div style={{ marginTop: '8px', padding: '12px', backgroundColor: '#0C0E14', borderRadius: '4px', borderLeft: '3px solid #DAA520' }}>
                          <Text style={{ display: 'block', color: '#00A651' }}>+ Débito: $7,275.00 (Cuenta 115 - Inventario PT)</Text>
                          <Text style={{ display: 'block', color: '#F44336' }}>- Crédito: $7,275.00 (Cuenta 115 - Inventario Proceso)</Text>
                          <Text type="secondary" style={{ fontSize: '11px', marginTop: '4px', display: 'block' }}>Transacción Inmutable. Hash: tx_9f8d7e6c</Text>
                        </div>
                      </>
                    ),
                  }
                ]}
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};
