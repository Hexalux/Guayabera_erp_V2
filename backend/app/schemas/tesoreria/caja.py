"""
Schemas Pydantic para el módulo de Tesorería - Caja
Inspirado en CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from enum import Enum


class FormaPagoEnum(str, Enum):
    EFECTIVO = "EFECTIVO"
    CHEQUE = "CHEQUE"
    TRANSFERENCIA = "TRANSFERENCIA"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    NOTA_CREDITO = "NOTA_CREDITO"


class TipoValorEnum(str, Enum):
    CHEQUE = "CHEQUE"
    PAGARE = "PAGARE"
    TARJETA = "TARJETA"
    LETRA_CAMBIO = "LETRA_CAMBIO"


class TurnoEnum(str, Enum):
    MATUTINO = "MATUTINO"
    VESPERTINO = "VESPERTINO"
    NOCTURNO = "NOCTURNO"


class TipoCorteEnum(str, Enum):
    PARCIAL = "PARCIAL"
    TURNO = "TURNO"
    DIARIO = "DIARIO"
    GENERAL = "GENERAL"


# ==================== CAJA ====================

class CajaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    codigo: str = Field(..., min_length=1, max_length=20)
    sucursal_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    moneda: str = Field(default="USD", max_length=3)
    activo: bool = True


class CajaCreate(CajaBase):
    tenant_id: UUID


class CajaUpdate(BaseModel):
    nombre: Optional[str] = None
    responsable_id: Optional[UUID] = None
    activo: Optional[bool] = None


class CajaResponse(CajaBase):
    id: UUID
    tenant_id: UUID
    saldo_actual: float = 0.0
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== RECIBO DE CAJA ====================

class ReciboCajaBase(BaseModel):
    caja_id: UUID
    serie: str = Field(..., min_length=1, max_length=10)
    cliente_id: Optional[UUID] = None
    concepto: str = Field(default="", max_length=500)
    monto: float = Field(..., gt=0)
    forma_pago: FormaPagoEnum = FormaPagoEnum.EFECTIVO
    referencia: str = Field(default="", max_length=100)
    aplicar_a_cxc: bool = False
    factura_id: Optional[UUID] = None


class ReciboCajaCreate(ReciboCajaBase):
    tenant_id: UUID


class ReciboCajaAnular(BaseModel):
    motivo: str = Field(..., min_length=10, max_length=500)
    usuario_id: UUID


class ReciboCajaResponse(ReciboCajaBase):
    id: UUID
    tenant_id: UUID
    consecutivo: int
    numero_completo: str  # Ej: "A-000123"
    estado: str = "ACTIVO"
    fecha_emision: datetime
    fecha_anulacion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = None
    usuario_anulo: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# ==================== LIQUIDACIÓN SUCURSAL ====================

class LiquidacionSucursalBase(BaseModel):
    sucursal_id: UUID
    fecha: date
    efectivo: float = 0.0
    cheques: float = 0.0
    tarjetas: float = 0.0
    transferencias: float = 0.0


class LiquidacionSucursalCreate(LiquidacionSucursalBase):
    tenant_id: UUID
    usuario_id: UUID


class LiquidacionSucursalResponse(LiquidacionSucursalBase):
    id: UUID
    tenant_id: UUID
    total: float
    estado: str = "BORRADOR"
    fecha_creacion: datetime
    fecha_cierre: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== LIQUIDACIÓN VENDEDOR ====================

class LiquidacionVendedorBase(BaseModel):
    vendedor_id: UUID
    fecha_inicio: date
    fecha_fin: date
    ventas_contado: float = 0.0
    ventas_credito: float = 0.0
    cobros_realizados: float = 0.0
    anticipo_comisiones: float = 0.0


class LiquidacionVendedorCreate(LiquidacionVendedorBase):
    tenant_id: UUID
    usuario_id: UUID


class LiquidacionVendedorResponse(LiquidacionVendedorBase):
    id: UUID
    tenant_id: UUID
    comisiones_devengadas: float = 0.0
    neto_pagar: float = 0.0
    estado: str = "BORRADOR"
    fecha_creacion: datetime
    fecha_calculo: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== RECEPCIÓN DE VALORES ====================

class RecepcionValoresBase(BaseModel):
    caja_id: UUID
    tipo_valor: TipoValorEnum
    numero: str = Field(..., min_length=1, max_length=50)
    banco_librador: str = Field(..., min_length=1, max_length=200)
    monto: float = Field(..., gt=0)
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    cliente_id: Optional[UUID] = None
    observations: str = Field(default="", max_length=1000)


class RecepcionValoresCreate(RecepcionValoresBase):
    tenant_id: UUID


class RecepcionValoresResponse(RecepcionValoresBase):
    id: UUID
    tenant_id: UUID
    estado: str = "RECIBIDO"
    motivo_rebote: Optional[str] = None
    fecha_rebote: Optional[datetime] = None
    usuario_reboto: Optional[UUID] = None
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# ==================== ARQUEO DE CAJA ====================

class ArqueoCajaBase(BaseModel):
    caja_id: UUID
    usuario_id: UUID
    fecha_corte: datetime
    turno: TurnoEnum = TurnoEnum.MATUTINO
    efectivo_contado: float = 0.0
    cheques_monto: float = 0.0
    tarjetas_monto: float = 0.0
    otros_monto: float = 0.0
    total_sistema: float = 0.0


class ArqueoCajaCreate(ArqueoCajaBase):
    pass


class ArqueoCajaCerrar(BaseModel):
    usuario_id: UUID


class ArqueoCajaResponse(ArqueoCajaBase):
    id: UUID
    diferencia: float = 0.0
    estado: str = "ABIERTO"
    usuario_cierre: Optional[UUID] = None
    fecha_cierre: Optional[datetime] = None
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# ==================== CORTE DE CAJA ====================

class CorteCajaBase(BaseModel):
    caja_id: UUID
    usuario_id: UUID
    tipo_corte: TipoCorteEnum = TipoCorteEnum.PARCIAL
    turno: Optional[TurnoEnum] = None


class CorteCajaCreate(CorteCajaBase):
    pass


class CorteCajaFinalizar(BaseModel):
    total_efectivo: float = 0.0
    total_cheques: float = 0.0
    total_tarjetas: float = 0.0
    total_transferencias: float = 0.0
    observaciones: str = Field(default="", max_length=1000)
    usuario_id: UUID


class CorteCajaResponse(CorteCajaBase):
    id: UUID
    total_efectivo: float = 0.0
    total_cheques: float = 0.0
    total_tarjetas: float = 0.0
    total_transferencias: float = 0.0
    total_general: float = 0.0
    observaciones: str = ""
    estado: str = "EN_PROCESO"
    usuario_cierre: Optional[UUID] = None
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== REPORTES ====================

class ReporteArqueoCaja(BaseModel):
    caja_id: UUID
    caja_nombre: str
    fecha_corte: datetime
    turno: str
    efectivo_sistema: float
    efectivo_contado: float
    diferencia_efectivo: float
    cheques_monto: float
    tarjetas_monto: float
    total_sistema: float
    total_contado: float
    diferencia_total: float
    estado: str


class ReporteCorteCaja(BaseModel):
    caja_id: UUID
    caja_nombre: str
    tipo_corte: str
    turno: Optional[str]
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime]
    total_efectivo: float
    total_cheques: float
    total_tarjetas: float
    total_transferencias: float
    total_general: float
    estado: str


class ReporteRecibosCaja(BaseModel):
    caja_id: UUID
    caja_nombre: str
    serie: str
    consecutivo_inicial: int
    consecutivo_final: int
    total_activos: int
    total_anulados: int
    monto_total_activos: float
    monto_total_anulados: float
