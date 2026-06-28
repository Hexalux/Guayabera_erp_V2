import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Spin, message, Row, Col, Alert, Select, Space, Tag } from 'antd';
import { ClockCircleOutlined, WifiOutlined, DisconnectOutlined, ScanOutlined } from '@ant-design/icons';
import { hrService, Empleado } from '../../services/hrService';
import { biometricService } from '../../services/biometricService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

export const Checador: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(dayjs());
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [loading, setLoading] = useState(false);
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  
  // Para la simulación de quién está checando sin huella real
  const [selectedEmpleado, setSelectedEmpleado] = useState<string | null>(null);
  const [pendingQueue, setPendingQueue] = useState(JSON.parse(localStorage.getItem('offline_checks') || '[]').length);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(dayjs()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const updateOnlineStatus = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
    };
  }, []);

  useEffect(() => {
    if (isOnline) {
      hrService.getEmpleados().then(data => setEmpleados(data)).catch(() => {});
      // Tratar de vaciar cola
      biometricService.syncOfflineQueue().then(c => {
        if (c > 0) message.success(`Se sincronizaron ${c} asistencias atrasadas.`);
        setPendingQueue(JSON.parse(localStorage.getItem('offline_checks') || '[]').length);
      });
    }
  }, [isOnline]);

  const handleScan = async (tipo: 'entrada' | 'salida') => {
    if (!selectedEmpleado) {
      message.warning("Por favor selecciona un empleado para la simulación.");
      return;
    }

    setLoading(true);
    try {
      // 1. Escanear Huella (Pide al agente local o simula)
      message.info("Coloque su dedo en el lector...");
      await biometricService.scanFingerprint();
      
      // 2. Aquí idealmente compararíamos la huella escaneada con las del servidor
      // En la vida real, el servidor o el dispositivo hace el "match".
      // Para este MVP, asumiremos que si escaneó, es el empleado seleccionado.

      // 3. Registrar Asistencia
      await biometricService.clockInOrOut(selectedEmpleado, tipo);
      
      message.success(`Registro de ${tipo} guardado exitosamente.`);
      setSelectedEmpleado(null);
      setPendingQueue(JSON.parse(localStorage.getItem('offline_checks') || '[]').length);

    } catch (error) {
      message.error("Error al registrar asistencia");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-main)', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      
      <Card style={{ width: 600, backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', borderRadius: '12px', textAlign: 'center' }}>
        <div style={{ position: 'absolute', top: 16, right: 16 }}>
          {isOnline ? (
            <Tag color="green" icon={<WifiOutlined />}>ONLINE</Tag>
          ) : (
            <Tag color="red" icon={<DisconnectOutlined />}>OFFLINE</Tag>
          )}
        </div>

        <ClockCircleOutlined style={{ fontSize: '48px', color: 'var(--accent-primary)', marginBottom: '16px' }} />
        <Title level={1} style={{ color: 'var(--text-main)', margin: 0, fontSize: '64px' }}>
          {currentTime.format('HH:mm:ss')}
        </Title>
        <Text style={{ color: 'var(--text-secondary)', fontSize: '24px' }}>
          {currentTime.format('dddd, D MMMM YYYY')}
        </Text>

        <div style={{ marginTop: '40px' }}>
          <Alert
            message="Simulación de Biometría"
            description="Selecciona un empleado de la lista para simular su identidad biométrica."
            type="info"
            style={{ marginBottom: '20px', textAlign: 'left' }}
          />
          <Select 
            placeholder="Seleccionar Empleado (Simulación)" 
            style={{ width: '100%', marginBottom: '24px' }}
            value={selectedEmpleado}
            onChange={v => setSelectedEmpleado(v)}
            disabled={!isOnline && empleados.length === 0}
          >
            {empleados.map(e => <Option key={e.id} value={e.id}>{e.nombre_completo}</Option>)}
          </Select>

          <Spin spinning={loading}>
            <Row gutter={16}>
              <Col span={12}>
                <Button 
                  type="primary" 
                  size="large" 
                  block 
                  icon={<ScanOutlined />} 
                  style={{ height: '80px', fontSize: '20px', backgroundColor: '#00A651', borderColor: '#00A651' }}
                  onClick={() => handleScan('entrada')}
                >
                  Entrada
                </Button>
              </Col>
              <Col span={12}>
                <Button 
                  type="primary" 
                  danger
                  size="large" 
                  block 
                  icon={<ScanOutlined />} 
                  style={{ height: '80px', fontSize: '20px' }}
                  onClick={() => handleScan('salida')}
                >
                  Salida
                </Button>
              </Col>
            </Row>
          </Spin>
        </div>
      </Card>

      {!isOnline && pendingQueue > 0 && (
        <Alert 
          message={`${pendingQueue} registros pendientes de sincronización. Se enviarán cuando regrese la red.`} 
          type="warning" 
          showIcon 
          style={{ marginTop: '24px', width: 600 }}
        />
      )}
    </div>
  );
};
