import { api } from './authService'; // Reusing the configured axios instance

export interface CuentaContable {
  id?: string;
  codigo: string;
  nombre: string;
  nivel: number;
  tipo: string;
  naturaleza: string;
  es_agrupadora: boolean;
  cuenta_padre_id?: string;
  is_active?: boolean;
}

export interface MovimientoPoliza {
  id?: string;
  cuenta_id: string;
  cargo: number;
  abono: number;
  concepto: string;
  referencia?: string;
}

export interface PolizaContable {
  id?: string;
  numero: number;
  tipo: string;
  fecha: string;
  descripcion: string;
  estado: string;
  movimientos: MovimientoPoliza[];
  total_cargos?: number;
  total_abonos?: number;
}

export const financeService = {
  // Cuentas
  getCuentas: async () => {
    const response = await api.get('/finance/cuentas');
    return response.data;
  },
  
  createCuenta: async (cuenta: CuentaContable) => {
    const response = await api.post('/finance/cuentas', cuenta);
    return response.data;
  },

  // Polizas
  getPolizas: async () => {
    const response = await api.get('/finance/polizas');
    return response.data;
  },

  createPoliza: async (poliza: PolizaContable) => {
    const response = await api.post('/finance/polizas', poliza);
    return response.data;
  }
};
