from pydantic import BaseModel, Field
from typing import Optional, Decimal
from datetime import date, datetime
from enum import Enum

class TipoRevaluacion(str, Enum):
    AUTOMATICA = "automatica"
    MANUAL = "manual"

class EstadoRevaluacion(str, Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADA = "completada"
    ERROR = "error"

# --- Tipo de Cambio ---
class TipoCambioBase(BaseModel):
    moneda_origen: str  # Ej: USD
    moneda_destino: str  # Ej: EUR
    tasa_cambio: Decimal = Field(gt=0)
    fecha_vigencia: date
    fuente: Optional[str] = None  # Banco central, API externa
    activo: bool = True

class TipoCambioCreate(TipoCambioBase):
    pass

class TipoCambioResponse(TipoCambioBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Revaluación Automática ---
class RevaluacionAutomaticaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    frecuencia: str = "diaria"  # diaria, semanal, mensual
    monedas_objetivo: list = ["USD", "EUR"]  # Monedas a revaluar
    cuenta_contrapartida: int  # Cuenta contable de diferencia cambiaria
    activo: bool = True

class RevaluacionAutomaticaCreate(RevaluacionAutomaticaBase):
    pass

class RevaluacionAutomaticaResponse(RevaluacionAutomaticaBase):
    id: int
    ultima_ejecucion: Optional[datetime] = None
    proxima_ejecucion: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Ejecución de Revaluación ---
class EjecucionRevaluacionBase(BaseModel):
    revaluacion_id: int
    fecha_ejecucion: date
    tipo_cambio_referencia: Decimal
    notas: Optional[str] = None

class EjecucionRevaluacionCreate(EjecucionRevaluacionBase):
    pass

class EjecucionRevaluacionResponse(EjecucionRevaluacionBase):
    id: int
    estado: EstadoRevaluacion
    total_registros_procesados: int = 0
    monto_diferencia_cambiaria: Decimal = Field(default=0.0)
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Detalle de Revaluación ---
class DetalleRevaluacionBase(BaseModel):
    ejecucion_id: int
    cuenta_id: int
    saldo_original: Decimal
    saldo_revaluado: Decimal
    diferencia: Decimal
    tipo_cambio_aplicado: Decimal

class DetalleRevaluacionCreate(DetalleRevaluacionBase):
    pass

class DetalleRevaluacionResponse(DetalleRevaluacionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Valuación de Tipo de Cambio ---
class ValuacionTipoCambioBase(BaseModel):
    fecha_valuacion: date
    moneda: str
    tipo_cambio_oficial: Decimal
    tipo_cambio_mercado: Optional[Decimal] = None
    variacion_porcentual: Optional[Decimal] = None
    observaciones: Optional[str] = None

class ValuacionTipoCambioCreate(ValuacionTipoCambioBase):
    pass

class ValuacionTipoCambioResponse(ValuacionTipoCambioBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Parámetros de Revaluación ---
class ParametrosRevaluacionBase(BaseModel):
    tenant_id: int
    revaluacion_automatica_activa: bool = False
    hora_ejecucion: str = "23:00"  # Formato HH:MM
    tolerancia_variacion: Decimal = Field(default=5.0, description="Porcentaje máximo de variación antes de alertar")
    notificar_alertas: bool = True
    email_notificaciones: Optional[str] = None

class ParametrosRevaluacionCreate(ParametrosRevaluacionBase):
    pass

class ParametrosRevaluacionResponse(ParametrosRevaluacionBase):
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
