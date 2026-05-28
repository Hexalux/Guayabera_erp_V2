import axios from 'axios';
import { createAsyncThunk } from '@reduxjs/toolkit';

// Create axios instance
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
});

export const getUserFromToken = (token: string | null) => {
  if (!token) return null;

  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + (4 - base64.length % 4) % 4, '=');
    const payload = JSON.parse(atob(padded));
    return {
      id: payload.sub,
      email: payload.email,
      nombre_completo: payload.nombre_completo,
      user_type: payload.user_type,
      tipo_usuario: payload.tipo_usuario,
      tenant_id: payload.tenant_id,
    };
  } catch {
    return null;
  }
};

const getApiErrorDetail = (error: any) => error?.response?.data?.detail;

export const getApiErrorMessage = (error: any, fallback: string) => {
  const detail = getApiErrorDetail(error);

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || String(item))
      .join(', ');
  }

  return (
    (typeof detail === 'string' ? detail : detail?.message) ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
};

const getApiErrorPayload = (error: any, fallback: string) => {
  const detail = getApiErrorDetail(error);

  return {
    message: getApiErrorMessage(error, fallback),
    status: error?.response?.status,
    code: detail?.code || error?.response?.data?.code,
  };
};

// Request interceptor to add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const token = response.data.access_token;
      const user = response.data.user || getUserFromToken(token) || {
        email,
        tipo_usuario: 'normal',
        user_type: 'user',
      };
      return {
        user,
        token,
      };
    } catch (error: any) {
      return rejectWithValue(getApiErrorPayload(error, 'Error de autenticacion'));
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    { email, nombre_completo }: { email: string; password: string; nombre_completo: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.post('/auth/solicitar-registro', { email, nombre_completo });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(getApiErrorMessage(error, 'Error en el registro'));
    }
  }
);

export const recoverPassword = async (email: string) => {
  try {
    const response = await api.post('/auth/solicitar-recuperacion', { email });
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al recuperar la contrasena'));
  }
};

export const confirmRegistration = async (token: string, newPassword: string) => {
  try {
    const response = await api.post(`/auth/confirmar-registro/${token}`, { nueva_contrasena: newPassword });
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al confirmar el registro'));
  }
};

// API functions for managing tenants, users, and licenses
export const getTenants = async () => {
  try {
    const response = await api.get('/tenants/');
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al obtener tenants'));
  }
};

export const getUsers = async () => {
  try {
    const response = await api.get('/users/');
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al obtener usuarios'));
  }
};

export const getLicenses = async () => {
  try {
    const response = await api.get('/licencias/');
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al obtener licencias'));
  }
};

// Super Admin API functions
export const createTenant = async (tenantData: { name: string; subdomain: string; contact_email: string; descripcion: string }) => {
  try {
    const response = await api.post('/admin/crear-tenant', tenantData);
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al crear tenant'));
  }
};

export const inviteTenantAdmin = async (email: string, tenantId: string) => {
  try {
    const response = await api.post('/admin/invitar-tenant-admin', { email, tenant_id: tenantId });
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al invitar administrador'));
  }
};

export const getSuperAdminTenants = async () => {
  try {
    const response = await api.get('/admin/tenants');
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al obtener tenants'));
  }
};

export const getCorporations = async () => {
  try {
    const response = await api.get('/admin/corporaciones');
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al obtener corporaciones'));
  }
};

export const createCorporation = async (corpData: { name: string; descripcion?: string }) => {
  try {
    const response = await api.post('/admin/crear-corporacion', {
      nombre: corpData.name,
      descripcion: corpData.descripcion,
    });
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al crear corporacion'));
  }
};

export const createLicense = async (licenseData: any) => {
  try {
    const response = await api.post('/admin/crear-licencia', licenseData);
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al crear licencia'));
  }
};

export const activateTenant = async (tenantId: string) => {
  try {
    const response = await api.put(`/admin/activar-tenant/${tenantId}`);
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al activar tenant'));
  }
};

export const deactivateTenant = async (tenantId: string) => {
  try {
    const response = await api.put(`/admin/desactivar-tenant/${tenantId}`);
    return response.data;
  } catch (error: any) {
    throw new Error(getApiErrorMessage(error, 'Error al desactivar tenant'));
  }
};
