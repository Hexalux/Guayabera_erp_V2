import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/inventory`,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Categoria {
  id: string;
  nombre: string;
  codigo: string;
  descripcion?: string;
  parent_id?: string;
}

export interface UnidadMedida {
  id: string;
  nombre: string;
  abreviatura: string;
  is_active?: boolean;
}

export interface Producto {
  id: string;
  nombre: string;
  sku: string;
  categoria_id: string;
  unidad_medida_id?: string;
  tipo_producto?: string;
  composicion?: string;
  color_pantone?: string;
  gramaje?: number;
}

export interface Almacen {
  id: string;
  nombre: string;
  codigo: string;
}

export interface Ubicacion {
  id: string;
  almacen_id: string;
  nombre: string;
  parent_id?: string;
  pasillo?: string;
  estante?: string;
  rack?: string;
  nivel?: string;
}

export interface Lote {
  id: string;
  producto_id: string;
  numero_lote: string;
  ubicacion_id?: string;
  cantidad: number;
  variacion_tono?: string;
}

export interface Movimiento {
  id?: string;
  lote_id: string;
  ubicacion_origen_id?: string;
  ubicacion_destino_id?: string;
  cantidad: number;
  tipo_movimiento: 'entrada' | 'salida' | 'transferencia' | 'ajuste';
  referencia?: string;
}

// Service Methods
export const inventoryService = {
  // Almacenes
  getAlmacenes: async (): Promise<Almacen[]> => {
    const response = await api.get('/almacenes');
    return response.data;
  },
  createAlmacen: async (data: Partial<Almacen>): Promise<Almacen> => {
    const response = await api.post('/almacenes', data);
    return response.data;
  },

  // Ubicaciones
  getUbicaciones: async (): Promise<Ubicacion[]> => {
    const response = await api.get('/ubicaciones');
    return response.data;
  },
  createUbicacion: async (data: Partial<Ubicacion>): Promise<Ubicacion> => {
    const response = await api.post('/ubicaciones', data);
    return response.data;
  },

  // Categorias
  getCategorias: async (): Promise<Categoria[]> => {
    const response = await api.get('/categorias');
    return response.data;
  },
  createCategoria: async (data: Partial<Categoria>): Promise<Categoria> => {
    const response = await api.post('/categorias', data);
    return response.data;
  },

  // Unidades de Medida
  getUnidadesMedida: async (): Promise<UnidadMedida[]> => {
    const response = await api.get('/unidades-medida');
    return response.data;
  },
  createUnidadMedida: async (data: Partial<UnidadMedida>): Promise<UnidadMedida> => {
    const response = await api.post('/unidades-medida', data);
    return response.data;
  },

  // Productos
  getProductos: async (): Promise<Producto[]> => {
    const response = await api.get('/productos');
    return response.data;
  },
  createProducto: async (data: Partial<Producto>): Promise<Producto> => {
    const response = await api.post('/productos', data);
    return response.data;
  },

  // Lotes
  getLotes: async (): Promise<Lote[]> => {
    const response = await api.get('/lotes');
    return response.data;
  },
  createLote: async (data: Partial<Lote>): Promise<Lote> => {
    const response = await api.post('/lotes', data);
    return response.data;
  },

  // Movimientos (Trazabilidad)
  registrarMovimiento: async (data: Movimiento): Promise<Movimiento> => {
    const response = await api.post('/movimientos', data);
    return response.data;
  }
};
