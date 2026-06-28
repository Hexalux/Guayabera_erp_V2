import { api } from './authService';

export interface Cliente {
  id: string;
  razon_social: string;
  rfc?: string;
  email?: string;
  telefono?: string;
  direccion?: string;
  limite_credito: number;
}

export interface SesionCaja {
  id: string;
  cajero_id: string;
  fecha_apertura: string;
  fecha_cierre?: string;
  fondo_inicial: number;
  total_efectivo: number;
  total_tarjeta: number;
  diferencia: number;
  estado: string;
  notas?: string;
}

export interface VentaPOS {
  id: string;
  folio: string;
  fecha: string;
  cliente_id?: string;
  vendedor_id: string;
  sesion_id?: string;
  subtotal: number;
  iva: number;
  total: number;
  metodo_pago: string;
  estado: string;
  notas?: string;
  detalles: any[];
}

export const salesService = {
  getClientes: async (): Promise<Cliente[]> => {
    const response = await api.get('/sales/clientes');
    return response.data;
  },

  createCliente: async (cliente: Partial<Cliente>): Promise<Cliente> => {
    const response = await api.post('/sales/clientes', cliente);
    return response.data;
  },

  // Sesiones
  getSesiones: async (): Promise<SesionCaja[]> => {
    const response = await api.get('/sales/sesiones');
    return response.data;
  },
  getSesionActiva: async (): Promise<SesionCaja> => {
    const response = await api.get('/sales/sesiones/activa');
    return response.data;
  },
  openSesion: async (fondo_inicial: number, notas?: string): Promise<SesionCaja> => {
    const response = await api.post('/sales/sesiones/open', { fondo_inicial, notas });
    return response.data;
  },
  closeSesion: async (id: string, total_efectivo: number, total_tarjeta: number, notas?: string): Promise<SesionCaja> => {
    const response = await api.post(`/sales/sesiones/${id}/close`, { total_efectivo, total_tarjeta, notas });
    return response.data;
  },

  // POS
  getVentasPOS: async (): Promise<VentaPOS[]> => {
    const response = await api.get('/sales/pos');
    return response.data;
  },
  processCheckout: async (payload: any): Promise<VentaPOS> => {
    const response = await api.post('/sales/pos', payload);
    return response.data;
  }
};
