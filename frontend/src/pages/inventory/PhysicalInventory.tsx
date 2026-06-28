import React, { useEffect, useState } from 'react';
import { Card, Table, Typography, Select, Button, message, InputNumber, Space, Spin, Alert, Row, Col } from 'antd';
import { SyncOutlined, CheckCircleOutlined, SafetyOutlined } from '@ant-design/icons';
import { inventoryService, Lote, Ubicacion, Producto } from '../../services/inventoryService';

const { Title, Text } = Typography;
const { Option } = Select;

interface InventoryRow {
  lote_id: string;
  producto_nombre: string;
  numero_lote: string;
  cantidad_sistema: number;
  cantidad_fisica: number | null;
  diferencia: number;
}

export const PhysicalInventory: React.FC = () => {
  const [ubicaciones, setUbicaciones] = useState<Ubicacion[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  
  const [selectedUbicacion, setSelectedUbicacion] = useState<string | null>(null);
  const [inventoryData, setInventoryData] = useState<InventoryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchBaseData();
  }, []);

  const fetchBaseData = async () => {
    try {
      setLoading(true);
      const [ubics, prods, lts] = await Promise.all([
        inventoryService.getUbicaciones(),
        inventoryService.getProductos(),
        inventoryService.getLotes()
      ]);
      setUbicaciones(ubics);
      setProductos(prods);
      setLotes(lts);
    } catch (error) {
      message.error("Error al cargar datos base.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedUbicacion) {
      const lotesUbicacion = lotes.filter(l => l.ubicacion_id === selectedUbicacion);
      const rows: InventoryRow[] = lotesUbicacion.map(l => {
        const prod = productos.find(p => p.id === l.producto_id);
        return {
          lote_id: l.id,
          producto_nombre: prod?.nombre || 'Desconocido',
          numero_lote: l.numero_lote,
          cantidad_sistema: l.cantidad,
          cantidad_fisica: l.cantidad, // Por defecto asumimos que está bien
          diferencia: 0
        };
      });
      setInventoryData(rows);
    } else {
      setInventoryData([]);
    }
  }, [selectedUbicacion, lotes, productos]);

  const handleConteoChange = (val: number | null, record: InventoryRow) => {
    const newVal = val || 0;
    const diff = newVal - record.cantidad_sistema;
    
    setInventoryData(prev => prev.map(row => {
      if (row.lote_id === record.lote_id) {
        return { ...row, cantidad_fisica: newVal, diferencia: diff };
      }
      return row;
    }));
  };

  const handleProcesarAjustes = async () => {
    const ajustes = inventoryData.filter(row => row.diferencia !== 0);
    
    if (ajustes.length === 0) {
      return message.info("No hay diferencias reportadas para ajustar.");
    }

    try {
      setSubmitting(true);
      
      // Enviar cada ajuste
      for (const ajuste of ajustes) {
        await inventoryService.registrarMovimiento({
          lote_id: ajuste.lote_id,
          tipo_movimiento: 'ajuste',
          cantidad: ajuste.diferencia, // puede ser positivo o negativo
          ubicacion_origen_id: undefined,
          ubicacion_destino_id: undefined,
          referencia: `Auditoría Física - Diferencia de ${ajuste.diferencia}`
        });
      }

      message.success("Ajustes procesados y contabilizados correctamente.");
      // Recargar datos para refrescar la cantidad de los lotes
      await fetchBaseData();
      
    } catch (error: any) {
      message.error("Error procesando algunos ajustes: " + (error.response?.data?.detail || ""));
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    { title: 'Producto', dataIndex: 'producto_nombre', key: 'producto_nombre' },
    { title: 'Lote', dataIndex: 'numero_lote', key: 'numero_lote' },
    { 
      title: 'Cant. Sistema', 
      dataIndex: 'cantidad_sistema', 
      key: 'cantidad_sistema',
      render: (val: number) => <Text style={{ color: '#B8B9BD' }}>{val.toFixed(2)}</Text>
    },
    {
      title: 'Conteo Físico',
      key: 'conteo',
      render: (_: any, record: InventoryRow) => (
        <InputNumber 
          min={0} 
          precision={2} 
          value={record.cantidad_fisica} 
          onChange={(val) => handleConteoChange(val, record)}
          style={{ width: '120px' }}
        />
      )
    },
    {
      title: 'Diferencia',
      dataIndex: 'diferencia',
      key: 'diferencia',
      render: (val: number) => {
        let color = '#FFF';
        if (val > 0) color = '#00A651'; // Verde sobrante
        if (val < 0) color = '#F44336'; // Rojo faltante
        return <Text strong style={{ color }}>{val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}</Text>;
      }
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Title level={2} style={{ color: '#00A651', margin: 0 }}>
            <SafetyOutlined /> Auditoría de Inventario Físico
          </Title>
        </Col>
        <Col>
          <Button icon={<SyncOutlined />} onClick={fetchBaseData} loading={loading}>Actualizar</Button>
        </Col>
      </Row>

      <Card style={{ backgroundColor: '#161A24', borderColor: '#303030', marginBottom: '24px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text style={{ color: '#B8B9BD' }}>Selecciona la Ubicación (Rack/Pasillo) para iniciar el conteo ciego:</Text>
          <Select 
            placeholder="Seleccionar Ubicación" 
            style={{ width: '100%', maxWidth: '400px' }}
            onChange={(val) => setSelectedUbicacion(val)}
            value={selectedUbicacion}
            showSearch
            optionFilterProp="children"
          >
            {ubicaciones.map(u => (
              <Option key={u.id} value={u.id}>{u.nombre}</Option>
            ))}
          </Select>
        </Space>
      </Card>

      {selectedUbicacion && (
        <Card style={{ backgroundColor: '#161A24', borderColor: '#303030' }} bodyStyle={{ padding: 0 }}>
          <Alert 
            message="Instrucciones" 
            description="Ingresa la cantidad real encontrada en el rack. Las diferencias generarán automáticamente las pólizas contables correspondientes (Faltantes o Sobrantes)."
            type="info" 
            showIcon 
            style={{ margin: '24px' }}
          />

          <Table 
            dataSource={inventoryData} 
            columns={columns} 
            rowKey="lote_id" 
            pagination={false}
            className="dark-table"
            style={{ padding: '0 24px 24px 24px' }}
          />

          <div style={{ padding: '24px', textAlign: 'right', borderTop: '1px solid #303030' }}>
            <Button 
              type="primary" 
              size="large" 
              icon={<CheckCircleOutlined />} 
              onClick={handleProcesarAjustes}
              loading={submitting}
              style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
            >
              Procesar Ajustes y Contabilizar
            </Button>
          </div>
        </Card>
      )}

      <style>{`
        .dark-table .ant-table {
          background-color: transparent !important;
          color: #FFF !important;
        }
        .dark-table .ant-table-thead > tr > th {
          background-color: #0C0E14 !important;
          color: #B8B9BD !important;
          border-bottom: 1px solid #303030;
        }
        .dark-table .ant-table-tbody > tr > td {
          border-bottom: 1px solid #303030;
        }
        .dark-table .ant-table-tbody > tr:hover > td {
          background-color: #0C0E14 !important;
        }
      `}</style>
    </div>
  );
};
