import React, { useState, useEffect } from 'react';
import { Typography, Row, Col, Card, Tag, Button, message } from 'antd';
import { api } from '../../services/authService';

const { Title } = Typography;

export const ProyectosProduccion: React.FC = () => {
    const [proyectos, setProyectos] = useState<any[]>([]);

    useEffect(() => {
        const fetchProyectos = async () => {
            try {
                const res = await api.get('/production/v1/proyectos');
                setProyectos(res.data);
            } catch (error) {
                message.error('Error al cargar proyectos');
            }
        };
        fetchProyectos();
    }, []);

    const estados = ['planificacion', 'diseno', 'corte', 'maquila', 'terminado'];

    return (
        <div>
            <Title level={2}>Proyectos de Producción (Kanban)</Title>
            <div style={{ marginBottom: 16 }}>
                <Button type="primary">Nuevo Proyecto</Button>
            </div>
            <Row gutter={16}>
                {estados.map(estado => (
                    <Col span={4} key={estado} style={{ minHeight: '500px', backgroundColor: '#f0f2f5', padding: '10px', borderRadius: '5px', margin: '0 5px' }}>
                        <Title level={4} style={{ textAlign: 'center' }}>{estado.toUpperCase()}</Title>
                        {proyectos.filter(p => p.estado === estado).map(proyecto => (
                            <Card key={proyecto.id} style={{ marginBottom: '10px' }} size="small">
                                <strong>{proyecto.nombre}</strong>
                                <div><Tag color="blue">{proyecto.fecha_entrega || 'Sin fecha'}</Tag></div>
                            </Card>
                        ))}
                    </Col>
                ))}
            </Row>
        </div>
    );
};
