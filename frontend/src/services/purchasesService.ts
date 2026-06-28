import { api } from './authService';

export interface Proveedor {
    id: string;
    razon_social: string;
    rfc?: string;
    email?: string;
    telefono?: string;
    dias_credito: number;
    activo: boolean;
}

export interface ListaPrecioProveedor {
    id: string;
    proveedor_id: string;
    producto_textil_id: string;
    codigo_proveedor?: string;
    precio: number;
    moneda: string;
    factor_conversion: number;
}

export interface OrdenCompra {
    id: string;
    folio: string;
    fecha_emision: string;
    fecha_recepcion?: string;
    proveedor_id: string;
    comprador_id: string;
    estado: string; // rfq, emitida, recibida, cancelada
    subtotal: number;
    iva: number;
    total: number;
    notas?: string;
    detalles: DetalleOrdenCompra[];
}

export interface DetalleOrdenCompra {
    id: string;
    producto_textil_id: string;
    cantidad_solicitada: number;
    cantidad_recibida: number;
    precio_unitario: number;
    subtotal: number;
}

export interface OrdenCompraCreate {
    proveedor_id: string;
    notas?: string;
    detalles: {
        producto_textil_id: string;
        cantidad_solicitada: number;
        precio_unitario: number;
    }[];
}

export interface CuentaPorPagar {
    id: string;
    orden_compra_id: string;
    proveedor_id: string;
    proveedor_nombre?: string;
    folio_orden?: string;
    monto_original: number;
    monto_pagado: number;
    saldo_pendiente: number;
    fecha_emision: string;
    fecha_vencimiento: string;
    estado: string;
}

export interface PagoCxPCreate {
    cuenta_por_pagar_id: string;
    cuenta_bancaria_id: string;
    monto: number;
    referencia?: string;
}

export const purchasesService = {
    // Proveedores
    getProveedores: async (): Promise<Proveedor[]> => {
        const response = await api.get('/purchases/proveedores');
        return response.data;
    },
    createProveedor: async (data: Omit<Proveedor, 'id' | 'activo'>): Promise<Proveedor> => {
        const response = await api.post('/purchases/proveedores', data);
        return response.data;
    },

    // Listas de Precio
    getPreciosProveedor: async (proveedorId: string): Promise<ListaPrecioProveedor[]> => {
        const response = await api.get(`/purchases/proveedores/${proveedorId}/precios`);
        return response.data;
    },
    createPrecioProveedor: async (proveedorId: string, data: any): Promise<ListaPrecioProveedor> => {
        const response = await api.post(`/purchases/proveedores/${proveedorId}/precios`, data);
        return response.data;
    },

    // Órdenes de Compra
    getOrdenes: async (): Promise<OrdenCompra[]> => {
        const response = await api.get('/purchases/ordenes');
        return response.data;
    },
    createOrden: async (data: OrdenCompraCreate): Promise<OrdenCompra> => {
        const response = await api.post('/purchases/ordenes', data);
        return response.data;
    },
    confirmarRFQ: async (ordenId: string): Promise<any> => {
        const response = await api.post(`/purchases/ordenes/${ordenId}/confirmar`);
        return response.data;
    },
    recibirOrden: async (ordenId: string): Promise<any> => {
        const response = await api.post(`/purchases/ordenes/${ordenId}/recibir`);
        return response.data;
    },

    // Cuentas por Pagar
    getCxP: async (): Promise<CuentaPorPagar[]> => {
        const response = await api.get('/purchases/cxp/saldos');
        return response.data;
    },
    pagarCxP: async (data: PagoCxPCreate): Promise<any> => {
        const response = await api.post('/purchases/cxp/pagar', data);
        return response.data;
    }
};
