import React, { useState, useEffect } from 'react';
import { Card, Typography, DatePicker, Button, message, Space, Spin } from 'antd';
import { SettingOutlined, LockOutlined, SaveOutlined, UnlockOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

export const AccountingSettings: React.FC = () => {
  const [fechaCierre, setFechaCierre] = useState<dayjs.Dayjs | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await api.get('/accounting/settings/cierre');
      if (res.data.fecha_cierre_contable) {
        setFechaCierre(dayjs(res.data.fecha_cierre_contable));
      } else {
        setFechaCierre(null);
      }
    } catch (error) {
      message.error('Error al cargar configuración de cierre contable');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post('/accounting/settings/cierre', {
        fecha_cierre: fechaCierre ? fechaCierre.format('YYYY-MM-DD') : null
      });
      message.success('Fecha de bloqueo actualizada correctamente');
    } catch (error) {
      message.error('Error al guardar configuración');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}><Spin size="large" /></div>;

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Title level={2} style={{ color: '#2196F3', marginBottom: '8px' }}>
        <SettingOutlined /> Configuración Contable
      </Title>
      <Text style={{ color: '#B8B9BD', display: 'block', marginBottom: '24px' }}>
        Ajustes avanzados para el módulo financiero.
      </Text>

      <Card 
        title={<span style={{ color: '#FFF' }}><LockOutlined /> Bloqueo de Periodos Contables</span>}
        style={{ backgroundColor: '#161A24', borderColor: '#303030', maxWidth: 600 }}
        headStyle={{ borderBottom: '1px solid #303030' }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text style={{ color: '#B8B9BD', display: 'block', marginBottom: 8 }}>
            Establece una fecha límite. El sistema no permitirá la creación o modificación de pólizas, facturas ni movimientos con fecha anterior o igual a la fecha de bloqueo.
          </Text>
        </div>
        
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong style={{ color: '#FFF', display: 'block', marginBottom: 8 }}>Fecha de Bloqueo:</Text>
            <DatePicker 
              value={fechaCierre}
              onChange={(date) => setFechaCierre(date)}
              style={{ width: '100%', maxWidth: 300 }}
              placeholder="Seleccionar fecha"
              allowClear
              format="DD/MM/YYYY"
            />
          </div>
          
          <Space>
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              onClick={handleSave}
              loading={saving}
              style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
            >
              Guardar Cambios
            </Button>
            {fechaCierre && (
              <Button 
                danger 
                icon={<UnlockOutlined />} 
                onClick={() => {
                  setFechaCierre(null);
                }}
              >
                Remover Bloqueo
              </Button>
            )}
          </Space>
        </Space>
      </Card>
    </div>
  );
};
