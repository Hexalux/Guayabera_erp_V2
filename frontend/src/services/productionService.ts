import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/production`,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface RecetaProduccion {
  id: string;
  producto_padre_id: string;
  insumo_id: string;
  cantidad_requerida: number;
}

export interface OrdenProduccion {
  id: string;
  folio: string;
  producto_final_id: string;
  cantidad_programada: number;
  cantidad_producida: number;
  estado: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  costo_materia_prima?: number;
  costo_maquila_externa?: number;
  costo_total?: number;
}

export interface FinalizarOrdenRequest {
  cantidad_real_producida: number;
  costo_maquila_adicional?: number;
  maquilador_nombre?: string;
}

export const productionService = {
  getRecetas: async (): Promise<RecetaProduccion[]> => {
    const response = await api.get('/recetas');
    return response.data;
  },
  createReceta: async (data: Partial<RecetaProduccion>): Promise<RecetaProduccion> => {
    const response = await api.post('/recetas', data);
    return response.data;
  },
  getOrdenes: async (): Promise<OrdenProduccion[]> => {
    const response = await api.get('/ordenes');
    return response.data;
  },
  createOrden: async (data: Partial<OrdenProduccion>): Promise<OrdenProduccion> => {
    const response = await api.post('/ordenes', data);
    return response.data;
  },
  finalizarOrden: async (id: string, data: FinalizarOrdenRequest): Promise<OrdenProduccion> => {
    const response = await api.post(`/ordenes/${id}/finalizar`, data);
    return response.data;
  }
};
