import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Spin, List, Avatar, Button, Modal, Form, Input, message } from 'antd';
import { NotificationOutlined, PlusOutlined, TeamOutlined, CalendarOutlined } from '@ant-design/icons';
import { hrService, NoticiaHR } from '../../services/hrService';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';

const { Title, Text, Paragraph } = Typography;

export const HRDashboard: React.FC = () => {
  const [noticias, setNoticias] = useState<NoticiaHR[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchNoticias = async () => {
    try {
      setLoading(true);
      const data = await hrService.getNoticias();
      setNoticias(data);
    } catch (error) {
      message.error("Error cargando noticias");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNoticias();
  }, []);

  const handleCreateNoticia = async (values: any) => {
    try {
      await hrService.createNoticia(values);
      message.success("Noticia publicada exitosamente");
      setIsModalVisible(false);
      form.resetFields();
      fetchNoticias();
    } catch (error) {
      message.error("Error publicando noticia");
    }
  };

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', color: 'var(--text-main)' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: 'var(--text-main)', margin: 0 }}>
            <TeamOutlined /> Portal del Empleado (RRHH)
          </Title>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={16}>
          <Card 
            title={<Text style={{ color: 'var(--text-main)', fontSize: '18px' }}><NotificationOutlined /> Tablón de Anuncios Oficiales</Text>}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Publicar</Button>}
            style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px' }}
            headStyle={{ borderBottom: '1px solid var(--border-color)' }}
          >
            <Spin spinning={loading}>
              <List
                itemLayout="vertical"
                dataSource={noticias}
                renderItem={item => (
                  <List.Item
                    key={item.id}
                    style={{ borderBottom: '1px solid var(--border-color)' }}
                  >
                    <List.Item.Meta
                      avatar={<Avatar style={{ backgroundColor: 'var(--accent-primary)' }}>{item.autor.charAt(0)}</Avatar>}
                      title={<Text style={{ color: 'var(--accent-primary)', fontSize: '16px', fontWeight: 'bold' }}>{item.titulo}</Text>}
                      description={<Text style={{ color: 'var(--text-secondary)' }}>Por {item.autor} el {dayjs(item.created_at).format('DD/MM/YYYY')}</Text>}
                    />
                    <Paragraph style={{ color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>
                      {item.contenido}
                    </Paragraph>
                  </List.Item>
                )}
                locale={{ emptyText: <Text style={{ color: 'var(--text-secondary)' }}>No hay noticias recientes.</Text> }}
              />
            </Spin>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card 
            title={<Text style={{ color: 'var(--text-main)' }}>Accesos Rápidos</Text>}
            style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px', marginBottom: '24px' }}
            headStyle={{ borderBottom: '1px solid var(--border-color)' }}
          >
            <Button block size="large" icon={<TeamOutlined />} onClick={() => navigate('/hr/directory')} style={{ marginBottom: '16px' }}>
              Directorio y Organigrama
            </Button>
            <Button block size="large" icon={<CalendarOutlined />} onClick={() => navigate('/hr/timeoff')}>
              Mis Vacaciones / Ausencias
            </Button>
          </Card>
        </Col>
      </Row>

      <Modal
        title="Nueva Publicación Oficial"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateNoticia}>
          <Form.Item name="titulo" label="Título del Anuncio" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="contenido" label="Contenido (Mensaje a la empresa)" rules={[{ required: true }]}>
            <Input.TextArea rows={6} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block style={{ backgroundColor: 'var(--accent-primary)' }}>
            Publicar
          </Button>
        </Form>
      </Modal>
    </div>
  );
};
