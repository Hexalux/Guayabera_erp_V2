import { api } from './authService';

export interface Departamento {
  id: string;
  nombre: string;
}

export interface Empleado {
  id: string;
  codigo: string;
  nombre_completo: string;
  email?: string;
  telefono?: string;
  puesto?: string;
  departamento_id?: string;
  jefe_id?: string;
  is_active: boolean;
  huella_template?: string;
  requiere_asistencia?: boolean;
}

export interface RegistroAsistencia {
  id: string;
  empleado_id: string;
  tipo: string;
  metodo: string;
  offline_sync: boolean;
  fecha_hora: string;
  created_at: string;
}

export interface NoticiaHR {
  id: string;
  titulo: string;
  contenido: string;
  autor: string;
  created_at: string;
}

export interface ControlVacaciones {
  id: string;
  empleado_id: string;
  fecha_inicio: string;
  fecha_fin: string;
  dias_solicitados: number;
  estado: string;
  created_at: string;
}

export interface Inasistencia {
  id: string;
  empleado_id: string;
  fecha: string;
  motivo?: string;
  justificada: boolean;
  created_at: string;
}

export interface Nomina {
  id: string;
  empleado_id: string;
  fecha_pago: string;
  total_percepciones: number;
  total_deducciones: number;
  neto_pagado: number;
  uuid_cfdi?: string;
  url_xml?: string;
  url_pdf?: string;
  estado_timbrado: string;
  created_at: string;
}

export interface CalculoNominaResponse {
  ingreso_gravable: number;
  isr_retenido: number;
  cuota_imss: number;
  total_percepciones: number;
  total_deducciones: number;
  neto_pagado: number;
}

export interface CalculoNominaRequest {
  empleado_id: string;
  dias_periodo: number;
  faltas: number;
}

export interface ParametroFiscal {
  anio: number;
  uma: number;
  smi: number;
}

export interface TablaISR {
  id: string;
  periodicidad: string;
  limite_inferior: number;
  limite_superior: number;
  cuota_fija: number;
  porcentaje: number;
}

export interface SATCatalogo {
  id: string;
  clave: string;
  descripcion: string;
  is_active: boolean;
}

export interface ContratoLaboral {
  id?: string;
  empleado_id: string;
  tipo_contrato: string;
  tipo_jornada_id?: string;
  periodicidad_pago_id?: string;
  fecha_inicio: string;
  fecha_fin?: string;
  salario_diario: number;
  salario_diario_integrado?: number;
  salario_base_cotizacion?: number;
  dias_laborables: number;
}

export const hrService = {
  getDepartamentos: async (): Promise<Departamento[]> => {
    const response = await api.get('/hr/departamentos');
    return response.data;
  },
  createDepartamento: async (data: any): Promise<Departamento> => {
    const response = await api.post('/hr/departamentos', data);
    return response.data;
  },
  
  getEmpleados: async (): Promise<Empleado[]> => {
    const response = await api.get('/hr/empleados');
    return response.data;
  },
  createEmpleado: async (data: any): Promise<Empleado> => {
    const response = await api.post('/hr/empleados', data);
    return response.data;
  },
  updateEmpleado: async (id: string, data: any): Promise<Empleado> => {
    const response = await api.put(`/hr/empleados/${id}`, data);
    return response.data;
  },

  getNoticias: async (): Promise<NoticiaHR[]> => {
    const response = await api.get('/hr/noticias');
    return response.data;
  },
  createNoticia: async (data: any): Promise<NoticiaHR> => {
    const response = await api.post('/hr/noticias', data);
    return response.data;
  },

  getVacaciones: async (): Promise<ControlVacaciones[]> => {
    const response = await api.get('/hr/vacaciones');
    return response.data;
  },
  requestVacaciones: async (data: any): Promise<ControlVacaciones> => {
    const response = await api.post('/hr/vacaciones', data);
    return response.data;
  },
  approveVacaciones: async (id: string): Promise<ControlVacaciones> => {
    const response = await api.put(`/hr/vacaciones/${id}/approve`);
    return response.data;
  },
  rejectVacaciones: async (id: string): Promise<ControlVacaciones> => {
    const response = await api.put(`/hr/vacaciones/${id}/reject`);
    return response.data;
  },

  getInasistencias: async (): Promise<Inasistencia[]> => {
    const response = await api.get('/hr/inasistencias');
    return response.data;
  },
  registrarInasistencia: async (data: any): Promise<Inasistencia> => {
    const response = await api.post('/hr/inasistencias', data);
    return response.data;
  },

  // Asistencia y Biometría
  enrollHuella: async (empleado_id: string, template_base64: string): Promise<Empleado> => {
    const response = await api.post('/hr/asistencia/enroll', { empleado_id, template_base64 });
    return response.data;
  },
  checkAsistencia: async (data: any): Promise<RegistroAsistencia> => {
    const response = await api.post('/hr/asistencia/check', data);
    return response.data;
  },
  syncAsistenciasOffline: async (registros: any[]): Promise<RegistroAsistencia[]> => {
    const response = await api.post('/hr/asistencia/sync', registros);
    return response.data;
  },
  getAsistencias: async (): Promise<RegistroAsistencia[]> => {
    const response = await api.get('/hr/asistencia');
    return response.data;
  },

  // Nóminas
  getNominas: async (): Promise<Nomina[]> => {
    const response = await api.get('/hr/nominas');
    return response.data;
  },
  createNomina: async (data: any): Promise<Nomina> => {
    const response = await api.post('/hr/nominas', data);
    return response.data;
  },
  calcularNomina: async (data: CalculoNominaRequest): Promise<CalculoNominaResponse> => {
    const response = await api.post('/hr/nominas/calcular', data);
    return response.data;
  },
  timbrarNomina: async (nominaId: string): Promise<any> => {
    const response = await api.post(`/hr/nominas/${nominaId}/timbrar`);
    return response.data;
  },

  // Contratos
  getContratosEmpleado: async (empleado_id: string): Promise<ContratoLaboral[]> => {
    const response = await api.get(`/hr/empleados/${empleado_id}/contratos`);
    return response.data;
  },
  createContrato: async (data: any): Promise<ContratoLaboral> => {
    const response = await api.post('/hr/contratos', data);
    return response.data;
  },

  // Catálogos SAT
  getSATPercepciones: async (): Promise<SATCatalogo[]> => {
    const response = await api.get('/hr/catalogos/sat/percepciones');
    return response.data;
  },
  getSATDeducciones: async (): Promise<SATCatalogo[]> => {
    const response = await api.get('/hr/catalogos/sat/deducciones');
    return response.data;
  },

  // Fiscal
  getParametrosFiscales: async (anio: number): Promise<ParametroFiscal> => {
    const response = await api.get(`/hr/parametros-fiscales/${anio}`);
    return response.data;
  },
  getTablasISR: async (anio: number): Promise<TablaISR[]> => {
    const response = await api.get(`/hr/tablas-isr/${anio}`);
    return response.data;
  }
};
