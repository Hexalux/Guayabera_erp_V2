from pydantic import BaseModel, Field
from typing import Optional, List, Decimal
from datetime import date, datetime
from enum import Enum

class TipoGasto(str, Enum):
    OPERATIVO = "operativo"
    VIAJE = "viaje"
    NOMINA = "nomina"
    DEPRECIACION = "depreciacion"
    OTRO = "otro"

class EstadoGasto(str, Enum):
    BORRADOR = "borrador"
    PENDIENTE_APROBACION = "pendiente_aprobacion"
    APROBADO = "aprobado"
    PAGADO = "pagado"
    CANCELADO = "cancelado"

# --- Categoría de Gasto ---
class CategoriaGastoBase(BaseModel):
    nombre: str
    codigo: str
    cuenta_contable_id: Optional[int] = None
    requiere_centro_costo: bool = True
    activo: bool = True

class CategoriaGastoCreate(CategoriaGastoBase):
    pass

class CategoriaGastoResponse(CategoriaGastoBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Gasto ---
class GastoBase(BaseModel):
    descripcion: str
    fecha: date
    monto: Decimal
    tipo_gasto: TipoGasto = TipoGasto.OPERATIVO
    categoria_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    proveedor_id: Optional[int] = None
    factura_numero: Optional[str] = None
    estado: EstadoGasto = EstadoGasto.BORRADOR
    notas: Optional[str] = None

class GastoCreate(GastoBase):
    pass

class GastoUpdate(BaseModel):
    estado: Optional[EstadoGasto] = None
    notas: Optional[str] = None

class GastoResponse(GastoBase):
    id: int
    creado_por: int
    aprobado_por: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Gasto de Viaje ---
class GastoViajeBase(BaseModel):
    empleado_id: int
    fecha_inicio: date
    fecha_fin: date
    destino: str
    motivo: str
    presupuesto_estimado: Decimal = Field(default=0.0, ge=0)
    estado: EstadoGasto = EstadoGasto.BORRADOR

class GastoViajeCreate(GastoViajeBase):
    pass

class GastoViajeResponse(GastoViajeBase):
    id: int
    total_gastos: Decimal = Field(default=0.0)
    created_at: datetime
    
    class Config:
        from_attributes = True

class GastoViajeDetalleBase(BaseModel):
    gasto_viaje_id: int
    concepto: str
    fecha: date
    monto: Decimal
    comprobante: Optional[str] = None

class GastoViajeDetalleCreate(GastoViajeDetalleBase):
    pass

class GastoViajeDetalleResponse(GastoViajeDetalleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Nómina Gasto ---
class NominaGastoBase(BaseModel):
    periodo_inicio: date
    periodo_fin: date
    total_sueldos: Decimal
    total_impuestos: Decimal = Field(default=0.0)
    total_deducciones: Decimal = Field(default=0.0)
    total_neto: Decimal
    departamento_id: Optional[int] = None

class NominaGastoCreate(NominaGastoBase):
    pass

class NominaGastoResponse(NominaGastoBase):
    id: int
    procesado: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Depreciación ---
class DepreciacionActivoBase(BaseModel):
    activo_fijo_id: int
    descripcion: str
    vida_util_meses: int
    valor_original: Decimal
    valor_residual: Decimal = Field(default=0.0)
    metodo_depreciacion: str = "linea_recta"  # linea_recta, saldo_decreciente

class DepreciacionActivoCreate(DepreciacionActivoBase):
    pass

class DepreciacionActivoResponse(DepreciacionActivoBase):
    id: int
    depreciacion_acumulada: Decimal = Field(default=0.0)
    valor_libros: Decimal
    ultima_depreciacion: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Reclasificación ---
class ReclasificacionGastoBase(BaseModel):
    gasto_origen_id: int
    gasto_destino_id: int
    monto: Decimal
    justificacion: str
    autorizado_por: int

class ReclasificacionGastoCreate(ReclasificacionGastoBase):
    pass

class ReclasificacionGastoResponse(ReclasificacionGastoBase):
    id: int
    fecha: datetime
    aprobada: bool = False
    
    class Config:
        from_attributes = True

# --- Presupuesto ---
class PresupuestoGastoBase(BaseModel):
    categoria_id: int
    centro_costo_id: Optional[int] = None
    anio: int
    mes: int
    monto_presupuestado: Decimal
    comentarios: Optional[str] = None

class PresupuestoGastoCreate(PresupuestoGastoBase):
    pass

class PresupuestoGastoResponse(PresupuestoGastoBase):
    id: int
    monto_ejecutado: Decimal = Field(default=0.0)
    variacion: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True
