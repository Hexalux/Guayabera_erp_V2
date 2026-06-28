import React, { useEffect, useState } from 'react';
import { Card, Typography, Table, Row, Col, Tabs, Statistic, message } from 'antd';
import { SettingOutlined, CalculatorOutlined, BankOutlined } from '@ant-design/icons';
import { hrService, ParametroFiscal, TablaISR } from '../../services/hrService';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export const FiscalConfig: React.FC = () => {
  const [parametros, setParametros] = useState<ParametroFiscal | null>(null);
  const [tablasISR, setTablasISR] = useState<TablaISR[]>([]);
  const [loading, setLoading] = useState(false);
  const anioActual = 2024; // O dinámico

  const fetchFiscalData = async () => {
    try {
      setLoading(true);
      const [params, isr] = await Promise.all([
        hrService.getParametrosFiscales(anioActual),
        hrService.getTablasISR(anioActual)
      ]);
      setParametros(params);
      setTablasISR(isr);
    } catch (error) {
      message.error("Error cargando configuración fiscal (UMA o Tablas ISR)");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiscalData();
  }, []);

  const columnsISR = [
    { title: 'Límite Inferior ($)', dataIndex: 'limite_inferior', key: 'li', render: (v: number) => v.toFixed(2) },
    { title: 'Límite Superior ($)', dataIndex: 'limite_superior', key: 'ls', render: (v: number) => v.toFixed(2) },
    { title: 'Cuota Fija ($)', dataIndex: 'cuota_fija', key: 'cf', render: (v: number) => v.toFixed(2) },
    { title: '% Excedente', dataIndex: 'porcentaje', key: 'p', render: (v: number) => `${v.toFixed(2)}%` }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <SettingOutlined /> Configuración Fiscal y Tablas ({anioActual})
          </Title>
        </Col>
      </Row>

      <Card style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}>
        <Tabs defaultActiveKey="1">
          <TabPane tab={<span><BankOutlined /> UMA y Salarios Mínimos</span>} key="1">
            <Row gutter={16}>
              <Col span={8}>
                <Card bordered={false} style={{ backgroundColor: 'var(--bg-main)', textAlign: 'center' }}>
                  <Statistic 
                    title="Valor UMA Diario" 
                    value={parametros?.uma || 0} 
                    precision={2} 
                    prefix="$" 
                    valueStyle={{ color: 'var(--accent-primary)', fontWeight: 'bold' }} 
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card bordered={false} style={{ backgroundColor: 'var(--bg-main)', textAlign: 'center' }}>
                  <Statistic 
                    title="Salario Mínimo General (SMI)" 
                    value={parametros?.smi || 0} 
                    precision={2} 
                    prefix="$" 
                    valueStyle={{ color: 'var(--accent-primary)', fontWeight: 'bold' }} 
                  />
                </Card>
              </Col>
            </Row>
            <div style={{ marginTop: '16px' }}>
              <Text type="secondary">Nota: Los valores se actualizan por ley cada año. Asegúrese de mantenerlos al día para cálculos correctos de IMSS e ISR.</Text>
            </div>
          </TabPane>
          <TabPane tab={<span><CalculatorOutlined /> Tablas de Retención de ISR</span>} key="2">
            <div style={{ marginBottom: '16px' }}>
              <Text type="secondary">Tabla de tarifas del Artículo 96 de la LISR (Periodicidad: Quincenal)</Text>
            </div>
            <Table 
              dataSource={tablasISR} 
              columns={columnsISR} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
              pagination={false}
            />
          </TabPane>
        </Tabs>
      </Card>

      <style>{`
        .dark-table .ant-table { background-color: transparent !important; color: var(--text-main) !important; }
        .dark-table .ant-table-thead > tr > th { background-color: var(--bg-main) !important; color: var(--text-secondary) !important; border-bottom: 1px solid var(--border-color); }
        .dark-table .ant-table-tbody > tr > td { border-bottom: 1px solid var(--border-color); }
        .dark-table .ant-table-tbody > tr:hover > td { background-color: var(--bg-main) !important; }
      `}</style>
    </div>
  );
};
