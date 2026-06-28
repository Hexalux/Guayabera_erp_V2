import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Input, Button, Table, Typography, Space, Select, Modal, message, Statistic, Tag, Divider } from 'antd';
import { ShoppingCartOutlined, ScanOutlined, CreditCardOutlined, MoneyCollectOutlined, BankOutlined, DeleteOutlined, SafetyCertificateOutlined, LockOutlined, UnlockOutlined } from '@ant-design/icons';
import { api } from '../../services/authService';
import { salesService, SesionCaja } from '../../services/salesService';

const { Title, Text } = Typography;
const { Option } = Select;

interface Lote {
  id: string;
  numero_lote: string;
  cantidad: number;
  producto?: {
    nombre: string;
    sku: string;
    precio_venta_sugerido: number;
  };
}

interface CartItem {
  lote_id: string;
  numero_lote: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export const PointOfSale: React.FC = () => {
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('EFECTIVO');
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [session, setSession] = useState<SesionCaja | null>(null);
  const [sessionModalVisible, setSessionModalVisible] = useState(false);
  const [fondoInicial, setFondoInicial] = useState(0);
  const [closeSessionModalVisible, setCloseSessionModalVisible] = useState(false);
  const [totalEfectivo, setTotalEfectivo] = useState(0);
  const [totalTarjeta, setTotalTarjeta] = useState(0);
  const [clientes, setClientes] = useState<any[]>([]);
  const [selectedClienteId, setSelectedClienteId] = useState<string | undefined>(undefined);

  useEffect(() => {
    fetchLotes();
    checkSession();
    fetchClientes();
  }, []);

  const fetchClientes = async () => {
    try {
      const res = await salesService.getClientes();
      setClientes(res);
    } catch (e) {
      console.error(e);
    }
  };

  const checkSession = async () => {
    try {
      const activa = await salesService.getSesionActiva();
      setSession(activa);
    } catch (error: any) {
      if (error.response && error.response.status === 404) {
        setSession(null);
        setSessionModalVisible(true);
      } else {
        console.error("Error fetching active session", error);
      }
    }
  };

  const handleOpenSession = async () => {
    try {
      const nuevaSesion = await salesService.openSesion(fondoInicial, "Apertura de turno");
      setSession(nuevaSesion);
      setSessionModalVisible(false);
      message.success("Sesión abierta correctamente");
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Error al abrir sesión");
    }
  };

  const handleCloseSession = async () => {
    if (!session) return;
    try {
      await salesService.closeSesion(session.id, totalEfectivo, totalTarjeta, "Cierre manual");
      setSession(null);
      setCloseSessionModalVisible(false);
      message.success("Sesión cerrada correctamente");
      setSessionModalVisible(true);
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Error al cerrar sesión");
    }
  };

  const fetchLotes = async () => {
    try {
      // Endpoint que asume que lotes trae la data del producto asociado. (Simulado por ahora si no existe el endpoint exacto)
      const response = await api.get('/inventory/lotes');
      setLotes(response.data);
    } catch (error) {
      console.error('Error cargando inventario', error);
      message.error('No se pudo cargar el inventario disponible.');
    }
  };

  const handleAddToCart = (lote: Lote) => {
    if (lote.cantidad <= 0) {
      message.warning('Lote sin existencias.');
      return;
    }
    
    // Por simplicidad del MVP asume que cuesta $250.00
    const precio = lote.producto?.precio_venta_sugerido || 250.00; 
    const existingItem = cart.find(item => item.lote_id === lote.id);

    if (existingItem) {
      if (existingItem.cantidad + 1 > lote.cantidad) {
        message.warning('Supera el stock disponible.');
        return;
      }
      const newCart = cart.map(item => 
        item.lote_id === lote.id 
          ? { ...item, cantidad: item.cantidad + 1, subtotal: (item.cantidad + 1) * item.precio_unitario } 
          : item
      );
      setCart(newCart);
    } else {
      setCart([
        ...cart, 
        {
          lote_id: lote.id,
          numero_lote: lote.numero_lote,
          nombre: lote.producto?.nombre || `Guayabera (Lote ${lote.numero_lote})`,
          cantidad: 1,
          precio_unitario: precio,
          subtotal: precio
        }
      ]);
    }
  };

  const removeFromCart = (lote_id: string) => {
    setCart(cart.filter(item => item.lote_id !== lote_id));
  };

  const cartSubtotal = cart.reduce((sum, item) => sum + item.subtotal, 0);
  const cartIVA = cartSubtotal * 0.16;
  const cartTotal = cartSubtotal + cartIVA;

  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setIsCheckingOut(true);
    
    try {
      const payload = {
        cliente_id: selectedClienteId || null,
        metodo_pago: paymentMethod,
        detalles: cart.map(item => ({
          lote_id: item.lote_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario
        }))
      };
      
      const res = await salesService.processCheckout(payload);
      message.success(`¡Venta completada! Ticket: ${res.folio}`);
      setCart([]);
      setSelectedClienteId(undefined);
      setModalVisible(false);
      fetchLotes(); // Recargar stock
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error procesando la venta.');
    } finally {
      setIsCheckingOut(false);
    }
  };

  const filteredLotes = lotes.filter(l => l.numero_lote.toLowerCase().includes(searchTerm.toLowerCase()));

  const columns = [
    { title: 'Artículo', dataIndex: 'nombre', key: 'nombre' },
    { title: 'Lote', dataIndex: 'numero_lote', key: 'numero_lote', render: (text: string) => <Tag color="#00A651">{text}</Tag> },
    { title: 'Cant.', dataIndex: 'cantidad', key: 'cantidad' },
    { title: 'Precio U.', dataIndex: 'precio_unitario', key: 'precio', render: (val: number) => `$${val.toFixed(2)}` },
    { title: 'Subtotal', dataIndex: 'subtotal', key: 'subtotal', render: (val: number) => `$${val.toFixed(2)}` },
    { 
      title: '', 
      key: 'action', 
      render: (_: any, record: CartItem) => (
        <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeFromCart(record.lote_id)} />
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0C0E14', minHeight: '100vh', color: '#FFF' }}>
      <Row gutter={24}>
        {/* Catálogo de Productos */}
        <Col xs={24} lg={14}>
          <Card 
            title={<span style={{ color: '#00A651', fontSize: '20px' }}>Punto de Venta POS</span>} 
            extra={
              session ? (
                <Space>
                  <Tag color="success" icon={<UnlockOutlined />}>Turno Abierto</Tag>
                  <Button type="primary" danger size="small" onClick={() => setCloseSessionModalVisible(true)}>Cerrar Turno</Button>
                </Space>
              ) : (
                <Tag color="error" icon={<LockOutlined />}>Caja Cerrada</Tag>
              )
            }
            style={{ backgroundColor: '#161A24', borderColor: '#303030', minHeight: '80vh' }}
            bordered={false}
          >
            <Input 
              size="large" 
              placeholder="Escanear código de barras o buscar lote..." 
              prefix={<ScanOutlined style={{ color: '#DAA520' }} />}
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030', marginBottom: '24px' }}
            />
            
            <Row gutter={[16, 16]}>
              {filteredLotes.map(lote => (
                <Col xs={24} sm={12} md={8} key={lote.id}>
                  <Card 
                    hoverable 
                    onClick={() => handleAddToCart(lote)}
                    style={{ backgroundColor: '#0C0E14', borderColor: '#303030', height: '100%' }}
                    bodyStyle={{ padding: '16px', textAlign: 'center' }}
                  >
                    <SafetyCertificateOutlined style={{ fontSize: '32px', color: '#DAA520', marginBottom: '12px' }} />
                    <Text style={{ display: 'block', color: '#FFF', fontWeight: 'bold' }}>Guayabera (Prod. ID)</Text>
                    <Text type="secondary" style={{ display: 'block', fontSize: '12px' }}>{lote.numero_lote}</Text>
                    <Divider style={{ margin: '8px 0', borderColor: '#303030' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <Text style={{ color: '#00A651', fontWeight: 'bold' }}>$250.00</Text>
                      <Tag color={lote.cantidad > 0 ? "success" : "error"}>{lote.cantidad} Disp.</Tag>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>

        {/* Carrito y Cobro */}
        <Col xs={24} lg={10}>
          <Card 
            title={<span style={{ color: '#DAA520' }}><ShoppingCartOutlined /> Ticket de Venta</span>} 
            style={{ backgroundColor: '#161A24', borderColor: '#303030', height: '100%' }}
          >
            <Table 
              dataSource={cart} 
              columns={columns} 
              pagination={false}
              rowKey="lote_id"
              size="small"
              className="dark-table"
              style={{ marginBottom: '24px' }}
            />
            
            <div style={{ backgroundColor: '#0C0E14', padding: '16px', borderRadius: '8px', border: '1px solid #303030' }}>
              <Row justify="space-between" style={{ marginBottom: '8px' }}>
                <Text style={{ color: '#B8B9BD' }}>Subtotal:</Text>
                <Text style={{ color: '#FFF' }}>${cartSubtotal.toFixed(2)}</Text>
              </Row>
              <Row justify="space-between" style={{ marginBottom: '8px' }}>
                <Text style={{ color: '#B8B9BD' }}>IVA (16%):</Text>
                <Text style={{ color: '#FFF' }}>${cartIVA.toFixed(2)}</Text>
              </Row>
              <Divider style={{ margin: '12px 0', borderColor: '#303030' }} />
              <Row justify="space-between" align="middle">
                <Text strong style={{ fontSize: '18px', color: '#FFF' }}>Total a Cobrar:</Text>
                <Text strong style={{ fontSize: '24px', color: '#00A651' }}>${cartTotal.toFixed(2)}</Text>
              </Row>
            </div>

            <Button 
              type="primary" 
              size="large" 
              block 
              disabled={cart.length === 0 || !session}
              onClick={() => setModalVisible(true)}
              style={{ marginTop: '24px', backgroundColor: '#00A651', borderColor: '#00A651', height: '50px', fontSize: '18px' }}
            >
              PROCEDER AL COBRO
            </Button>
          </Card>
        </Col>
      </Row>

      <Modal
        title={<span style={{ color: '#DAA520' }}>Confirmar Pago</span>}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        bodyStyle={{ backgroundColor: '#161A24', padding: '24px' }}
        className="dark-modal"
      >
        <Statistic 
          title={<span style={{ color: '#B8B9BD' }}>Total a Cobrar</span>} 
          value={cartTotal} 
          precision={2} 
          prefix="$" 
          valueStyle={{ color: '#00A651', fontSize: '32px' }} 
        />
        
        <Divider style={{ borderColor: '#303030' }} />

        <Text style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Cliente (Opcional, Obligatorio para Crédito)</Text>
        <Select 
          value={selectedClienteId} 
          onChange={setSelectedClienteId} 
          style={{ width: '100%', marginBottom: '16px' }} 
          size="large"
          placeholder="Seleccionar Cliente / Público General"
          allowClear
          dropdownStyle={{ backgroundColor: '#161A24', color: '#FFF' }}
        >
          {clientes.map(c => (
            <Option key={c.id} value={c.id}>{c.razon_social}</Option>
          ))}
        </Select>
        
        <Text style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Método de Pago</Text>
        <Select 
          value={paymentMethod} 
          onChange={setPaymentMethod} 
          style={{ width: '100%', marginBottom: '24px' }} 
          size="large"
          dropdownStyle={{ backgroundColor: '#161A24', color: '#FFF' }}
        >
          <Option value="EFECTIVO"><MoneyCollectOutlined /> Efectivo</Option>
          <Option value="TARJETA"><CreditCardOutlined /> Tarjeta (Crédito/Débito)</Option>
          <Option value="TRANSFERENCIA"><BankOutlined /> Transferencia SPEI</Option>
          <Option value="CRÉDITO"><CreditCardOutlined /> A Crédito (CxC)</Option>
        </Select>

        <Button 
          type="primary" 
          size="large" 
          block 
          loading={isCheckingOut}
          onClick={handleCheckout}
          style={{ backgroundColor: '#00A651', borderColor: '#00A651', height: '50px' }}
        >
          Confirmar y Emitir Ticket
        </Button>
      </Modal>

      <Modal
        title={<span style={{ color: '#DAA520' }}><LockOutlined /> Apertura de Caja</span>}
        open={sessionModalVisible}
        closable={false}
        maskClosable={false}
        footer={null}
        bodyStyle={{ backgroundColor: '#161A24', padding: '24px' }}
        className="dark-modal"
      >
        <Text style={{ color: '#B8B9BD', marginBottom: '16px', display: 'block' }}>
          Para poder registrar ventas, necesitas abrir una sesión de caja. Ingresa el fondo inicial (efectivo en caja al iniciar el turno).
        </Text>
        <Input 
          type="number" 
          prefix="$" 
          value={fondoInicial} 
          onChange={e => setFondoInicial(parseFloat(e.target.value) || 0)} 
          size="large"
          style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030', marginBottom: '24px' }}
        />
        <Button 
          type="primary" 
          block 
          size="large" 
          onClick={handleOpenSession}
          style={{ backgroundColor: '#00A651', borderColor: '#00A651' }}
        >
          Abrir Turno
        </Button>
      </Modal>

      <Modal
        title={<span style={{ color: '#DAA520' }}><LockOutlined /> Arqueo y Cierre de Caja</span>}
        open={closeSessionModalVisible}
        onCancel={() => setCloseSessionModalVisible(false)}
        footer={null}
        bodyStyle={{ backgroundColor: '#161A24', padding: '24px' }}
        className="dark-modal"
      >
        <Text style={{ color: '#B8B9BD', marginBottom: '16px', display: 'block' }}>
          Declara el dinero físico y comprobantes de tarjeta en caja.
        </Text>
        <div style={{ marginBottom: '16px' }}>
            <Text style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Total Efectivo Declarado:</Text>
            <Input 
              type="number" 
              prefix="$" 
              value={totalEfectivo} 
              onChange={e => setTotalEfectivo(parseFloat(e.target.value) || 0)} 
              size="large"
              style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }}
            />
        </div>
        <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: '#FFF', display: 'block', marginBottom: '8px' }}>Total Tarjeta Declarado:</Text>
            <Input 
              type="number" 
              prefix="$" 
              value={totalTarjeta} 
              onChange={e => setTotalTarjeta(parseFloat(e.target.value) || 0)} 
              size="large"
              style={{ backgroundColor: '#0C0E14', color: '#FFF', borderColor: '#303030' }}
            />
        </div>
        <Button 
          type="primary" 
          danger
          block 
          size="large" 
          onClick={handleCloseSession}
        >
          Confirmar Cierre de Turno
        </Button>
      </Modal>

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
        .ant-modal-content {
          background-color: #161A24 !important;
        }
        .ant-modal-header {
          background-color: #161A24 !important;
          border-bottom: 1px solid #303030 !important;
        }
        .ant-modal-title {
          color: #FFF !important;
        }
        .ant-select-selector {
          background-color: #0C0E14 !important;
          color: #FFF !important;
          border-color: #303030 !important;
        }
      `}</style>
    </div>
  );
};
