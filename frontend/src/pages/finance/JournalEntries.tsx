import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker, Typography, message, InputNumber } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { financeService, PolizaContable, MovimientoPoliza, CuentaContable } from '../../services/financeService';
import moment from 'moment';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const JournalEntries: React.FC = () => {
  const [polizas, setPolizas] = useState<PolizaContable[]>([]);
  const [cuentas, setCuentas] = useState<CuentaContable[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  
  const [movimientos, setMovimientos] = useState<MovimientoPoliza[]>([]);

  const fetchPolizas = async () => {
    setLoading(true);
    try {
      const data = await financeService.getPolizas();
      setPolizas(data);
    } catch (error) {
      message.error('Error al cargar las pólizas contables');
    } finally {
      setLoading(false);
    }
  };

  const fetchCuentas = async () => {
    try {
      const data = await financeService.getCuentas();
      // Only affectable accounts
      setCuentas(data.filter((c: CuentaContable) => !c.es_agrupadora));
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchPolizas();
    fetchCuentas();
  }, []);

  const handleOpenModal = () => {
    form.resetFields();
    setMovimientos([]);
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  const addMovimiento = () => {
    setMovimientos([...movimientos, { cuenta_id: '', cargo: 0, abono: 0, concepto: form.getFieldValue('descripcion') || '' }]);
  };

  const removeMovimiento = (index: number) => {
    const newMovs = [...movimientos];
    newMovs.splice(index, 1);
    setMovimientos(newMovs);
  };

  const updateMovimiento = (index: number, field: string, value: any) => {
    const newMovs = [...movimientos];
    (newMovs[index] as any)[field] = value;
    
    // Auto-balance if they input cargo, clear abono and vice versa
    if (field === 'cargo' && value > 0) newMovs[index].abono = 0;
    if (field === 'abono' && value > 0) newMovs[index].cargo = 0;
    
    setMovimientos(newMovs);
  };

  const handleCreate = async (values: any) => {
    if (movimientos.length < 2) {
      message.error('Una póliza requiere al menos dos movimientos.');
      return;
    }

    const totalCargos = movimientos.reduce((sum, m) => sum + (m.cargo || 0), 0);
    const totalAbonos = movimientos.reduce((sum, m) => sum + (m.abono || 0), 0);

    if (Math.abs(totalCargos - totalAbonos) > 0.01) {
      message.error(`La póliza está descuadrada. Cargos: $${totalCargos.toFixed(2)}, Abonos: $${totalAbonos.toFixed(2)}`);
      return;
    }

    const newPoliza: PolizaContable = {
      numero: values.numero,
      tipo: values.tipo,
      fecha: values.fecha.format('YYYY-MM-DD'),
      descripcion: values.descripcion,
      estado: 'aprobada', // Forcing apobada if balanced for MVP
      movimientos: movimientos
    };

    try {
      await financeService.createPoliza(newPoliza);
      message.success('Póliza creada exitosamente');
      setIsModalVisible(false);
      fetchPolizas();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al crear la póliza');
    }
  };

  const totalC = movimientos.reduce((sum, m) => sum + (m.cargo || 0), 0);
  const totalA = movimientos.reduce((sum, m) => sum + (m.abono || 0), 0);
  const diferencia = Math.abs(totalC - totalA);
  const cuadra = diferencia < 0.01;

  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
    },
    {
      title: 'Tipo / No.',
      key: 'numero',
      render: (_: any, record: PolizaContable) => `${record.tipo.toUpperCase()} - ${record.numero}`,
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
    {
      title: 'Cargos',
      dataIndex: 'total_cargos',
      key: 'total_cargos',
      render: (val: number) => `$${val?.toFixed(2)}`
    },
    {
      title: 'Abonos',
      dataIndex: 'total_abonos',
      key: 'total_abonos',
      render: (val: number) => `$${val?.toFixed(2)}`
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => (
        <span style={{ color: estado === 'aprobada' ? 'green' : 'orange' }}>{estado.toUpperCase()}</span>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3}>Pólizas Contables</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenModal}>
          Nueva Póliza
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={polizas}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="Crear Nueva Póliza"
        open={isModalVisible}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        width={900}
        okText="Guardar Póliza"
        cancelText="Cancelar"
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="fecha"
              label="Fecha"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
              initialValue={moment()}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="tipo"
              label="Tipo de Póliza"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
              initialValue="diario"
            >
              <Select>
                <Option value="diario">Diario</Option>
                <Option value="ingreso">Ingresos</Option>
                <Option value="egreso">Egresos</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="numero"
              label="Número"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} min={1} />
            </Form.Item>
          </div>

          <Form.Item
            name="descripcion"
            label="Concepto General"
            rules={[{ required: true }]}
          >
            <TextArea rows={2} />
          </Form.Item>

          <div style={{ marginTop: 24, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={5}>Movimientos (Asientos)</Title>
              <Button size="small" type="dashed" onClick={addMovimiento} icon={<PlusOutlined />}>
                Agregar Asiento
              </Button>
            </div>
            
            <table style={{ width: '100%', marginTop: 8, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #f0f0f0', textAlign: 'left' }}>
                  <th style={{ padding: '8px 0' }}>Cuenta</th>
                  <th>Concepto</th>
                  <th>Cargo</th>
                  <th>Abono</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {movimientos.map((mov, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #fafafa' }}>
                    <td style={{ padding: '8px 4px 8px 0' }}>
                      <Select
                        showSearch
                        style={{ width: '100%' }}
                        placeholder="Buscar cuenta"
                        value={mov.cuenta_id || undefined}
                        onChange={(v) => updateMovimiento(index, 'cuenta_id', v)}
                        optionFilterProp="children"
                      >
                        {cuentas.map(c => (
                          <Option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</Option>
                        ))}
                      </Select>
                    </td>
                    <td style={{ padding: '8px 4px' }}>
                      <Input 
                        value={mov.concepto} 
                        onChange={(e) => updateMovimiento(index, 'concepto', e.target.value)}
                      />
                    </td>
                    <td style={{ padding: '8px 4px' }}>
                      <InputNumber 
                        value={mov.cargo} 
                        onChange={(v) => updateMovimiento(index, 'cargo', v || 0)}
                        min={0}
                        style={{ width: 120 }}
                      />
                    </td>
                    <td style={{ padding: '8px 4px' }}>
                      <InputNumber 
                        value={mov.abono} 
                        onChange={(v) => updateMovimiento(index, 'abono', v || 0)}
                        min={0}
                        style={{ width: 120 }}
                      />
                    </td>
                    <td style={{ padding: '8px 0', textAlign: 'right' }}>
                      <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeMovimiento(index)} />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={2} style={{ textAlign: 'right', padding: '16px 8px', fontWeight: 'bold' }}>Totales:</td>
                  <td style={{ padding: '16px 4px', fontWeight: 'bold', color: !cuadra ? 'red' : 'inherit' }}>
                    ${totalC.toFixed(2)}
                  </td>
                  <td style={{ padding: '16px 4px', fontWeight: 'bold', color: !cuadra ? 'red' : 'inherit' }}>
                    ${totalA.toFixed(2)}
                  </td>
                  <td></td>
                </tr>
                {!cuadra && movimientos.length > 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'right', color: 'red' }}>
                      Diferencia: ${diferencia.toFixed(2)} (La póliza debe estar cuadrada)
                    </td>
                  </tr>
                )}
              </tfoot>
            </table>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default JournalEntries;
