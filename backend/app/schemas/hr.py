from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime

class DepartamentoBase(BaseModel):
    nombre: str

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoResponse(DepartamentoBase):
    id: str
    tenant_id: str
    
    model_config = ConfigDict(from_attributes=True)

class EmpleadoBase(BaseModel):
    codigo: str
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    nss: Optional[str] = None
    puesto: Optional[str] = None
    departamento_id: Optional[str] = None
    jefe_id: Optional[str] = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoUpdate(BaseModel):
    puesto: Optional[str] = None
    departamento_id: Optional[str] = None
    jefe_id: Optional[str] = None

class EmpleadoResponse(EmpleadoBase):
    id: str
    tenant_id: str
    is_active: bool
    
    archivo_contrato: Optional[str] = None
    archivo_nacimiento: Optional[str] = None
    archivo_curp: Optional[str] = None
    huella_template: Optional[str] = None
    requiere_asistencia: bool
    
    model_config = ConfigDict(from_attributes=True)

class ControlVacacionesBase(BaseModel):
    empleado_id: str
    fecha_inicio: date
    fecha_fin: date
    dias_solicitados: int

class ControlVacacionesCreate(ControlVacacionesBase):
    pass

class ControlVacacionesResponse(ControlVacacionesBase):
    id: str
    tenant_id: str
    estado: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class NoticiaHRBase(BaseModel):
    titulo: str
    contenido: str

class NoticiaHRCreate(NoticiaHRBase):
    pass

class NoticiaHRResponse(NoticiaHRBase):
    id: str
    tenant_id: str
    autor: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InasistenciaBase(BaseModel):
    empleado_id: str
    fecha: date
    motivo: Optional[str] = None
    justificada: bool = False

class InasistenciaCreate(InasistenciaBase):
    pass

class InasistenciaResponse(InasistenciaBase):
    id: str
    tenant_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RegistroAsistenciaBase(BaseModel):
    empleado_id: str
    tipo: str
    metodo: str
    offline_sync: bool = False
    fecha_hora: Optional[datetime] = None

class RegistroAsistenciaCreate(RegistroAsistenciaBase):
    pass

class RegistroAsistenciaResponse(RegistroAsistenciaBase):
    id: str
    tenant_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class HuellaEnroll(BaseModel):
    empleado_id: str
    template_base64: str

class NominaBase(BaseModel):
    empleado_id: str
    fecha_pago: date
    total_percepciones: float = 0.00
    total_deducciones: float = 0.00
    neto_pagado: float = 0.00
    estado_timbrado: Optional[str] = "pendiente"

class NominaCreate(NominaBase):
    pass

class NominaResponse(NominaBase):
    id: str
    tenant_id: str
    uuid_cfdi: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SATCatalogoBase(BaseModel):
    clave: str
    descripcion: str

class SATCatalogoResponse(SATCatalogoBase):
    id: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ContratoLaboralBase(BaseModel):
    empleado_id: str
    tipo_contrato: str = "indeterminado"
    tipo_jornada_id: Optional[str] = None
    periodicidad_pago_id: Optional[str] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    salario_diario: float
    salario_diario_integrado: Optional[float] = None
    salario_base_cotizacion: Optional[float] = None
    dias_laborables: int = 6

class ContratoLaboralCreate(ContratoLaboralBase):
    pass

class ContratoLaboralResponse(ContratoLaboralBase):
    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CalculoNominaRequest(BaseModel):
    empleado_id: str
    dias_periodo: int
    faltas: int = 0
    
class CalculoNominaResponse(BaseModel):
    ingreso_gravable: float
    isr_retenido: float
    cuota_imss: float
    total_percepciones: float
    total_deducciones: float
    neto_pagado: float

class ParametroFiscalResponse(BaseModel):
    anio: int
    uma: float
    smi: float
    model_config = ConfigDict(from_attributes=True)

class TablaISRResponse(BaseModel):
    id: str
    periodicidad: str
    limite_inferior: float
    limite_superior: float
    cuota_fija: float
    porcentaje: float
    model_config = ConfigDict(from_attributes=True)
