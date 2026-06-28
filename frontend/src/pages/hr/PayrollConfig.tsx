import React, { useEffect, useState } from 'react';
import { Card, Typography, Table, Row, Col, Tabs, Tag, message } from 'antd';
import { SettingOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { hrService, SATCatalogo } from '../../services/hrService';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export const PayrollConfig: React.FC = () => {
  const [percepciones, setPercepciones] = useState<SATCatalogo[]>([]);
  const [deducciones, setDeducciones] = useState<SATCatalogo[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchCatalogos = async () => {
    try {
      setLoading(true);
      const [percs, deds] = await Promise.all([
        hrService.getSATPercepciones(),
        hrService.getSATDeducciones()
      ]);
      setPercepciones(percs);
      setDeducciones(deds);
    } catch (error) {
      message.error("Error cargando catálogos del SAT");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalogos();
  }, []);

  const columns = [
    { title: 'Clave SAT', dataIndex: 'clave', key: 'clave', render: (text: string) => <Text strong>{text}</Text> },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion' },
    { 
      title: 'Estado', 
      dataIndex: 'is_active', 
      key: 'estado',
      render: (active: boolean) => active ? <Tag color="success">Activo</Tag> : <Tag color="default">Inactivo</Tag>
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <SettingOutlined /> Configuración de Nómina y Catálogos SAT
          </Title>
        </Col>
      </Row>

      <Card style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}>
        <Tabs defaultActiveKey="1">
          <TabPane tab={<span><CheckCircleOutlined /> Percepciones (CFDI 4.0)</span>} key="1">
            <div style={{ marginBottom: '16px' }}>
              <Text type="secondary"><InfoCircleOutlined /> Catálogo c_TipoPercepcion. Define los conceptos de pago para los empleados.</Text>
            </div>
            <Table 
              dataSource={percepciones} 
              columns={columns} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
          <TabPane tab={<span><InfoCircleOutlined /> Deducciones (CFDI 4.0)</span>} key="2">
            <div style={{ marginBottom: '16px' }}>
              <Text type="secondary"><InfoCircleOutlined /> Catálogo c_TipoDeduccion. Define los descuentos aplicados a la nómina del trabajador.</Text>
            </div>
            <Table 
              dataSource={deducciones} 
              columns={columns} 
              rowKey="id" 
              loading={loading}
              className="dark-table"
              pagination={{ pageSize: 10 }}
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
