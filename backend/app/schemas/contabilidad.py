from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal


class TipoCuentaEnum(str, Enum):
    ACTIVO = "activo"
    PASIVO = "pasivo"
    PATRIMONIO = "patrimonio"
    INGRESO = "ingreso"
    GASTO = "gasto"
    COSTO = "costo"


class NaturalezaCuentaEnum(str, Enum):
    DEUDORA = "deudora"
    ACREEDORA = "acreedora"


class EstadoAsientoEnum(str, Enum):
    BORRADOR = "borrador"
    REGISTRADO = "registrado"
    ANULADO = "anulado"


# ==================== CUENTAS CONTABLES ====================

class CuentaContableBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    tipo_cuenta: TipoCuentaEnum
    naturaleza: NaturalezaCuentaEnum = NaturalezaCuentaEnum.DEUDORA
    nivel: int = Field(default=1, ge=1)
    parent_id: Optional[str] = None
    es_movimiento: bool = True
    es_activa: bool = True
    requiere_centro_costo: bool = False
    requiere_tercero: bool = False
    permite_multimoneda: bool = False
    moneda_base: str = Field(default="USD", max_length=3)


class CuentaContableCreate(CuentaContableBase):
    pass


class CuentaContableUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_cuenta: Optional[TipoCuentaEnum] = None
    naturaleza: Optional[NaturalezaCuentaEnum] = None
    es_activa: Optional[bool] = None
    requiere_centro_costo: Optional[bool] = None
    requiere_tercero: Optional[bool] = None


class CuentaContableResponse(CuentaContableBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    children: List['CuentaContableResponse'] = []
    
    class Config:
        from_attributes = True


# ==================== CENTROS DE COSTO ====================

class CentroCostoBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    nivel: int = Field(default=1, ge=1)
    parent_id: Optional[str] = None
    es_activo: bool = True


class CentroCostoCreate(CentroCostoBase):
    pass


class CentroCostoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_activo: Optional[bool] = None


class CentroCostoResponse(CentroCostoBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    children: List['CentroCostoResponse'] = []
    
    class Config:
        from_attributes = True


# ==================== PERÍODOS CONTABLES ====================

class PeriodoContableBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    fecha_inicio: datetime
    fecha_fin: datetime
    es_anual: bool = False


class PeriodoContableCreate(PeriodoContableBase):
    pass


class PeriodoContableUpdate(BaseModel):
    esta_cerrado: Optional[bool] = None
    nombre: Optional[str] = None


class PeriodoContableResponse(PeriodoContableBase):
    id: str
    tenant_id: str
    esta_cerrado: bool
    cerrado_por: Optional[str] = None
    cerrado_en: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MOVIMIENTOS DE ASIENTO ====================

class MovimientoAsientoBase(BaseModel):
    cuenta_id: str
    debito: Decimal = Field(default=0, ge=0)
    credito: Decimal = Field(default=0, ge=0)
    centro_costo_id: Optional[str] = None
    tercero_id: Optional[str] = None
    tipo_tercero: Optional[str] = None
    descripcion: Optional[str] = None
    moneda: str = Field(default="USD", max_length=3)
    tasa_cambio: Decimal = Field(default=1.0, ge=0)
    valor_original: Optional[Decimal] = None
    orden: int = Field(default=0)
    
    @validator('debito', 'credito')
    def validate_no_both(cls, v, values):
        # Validación básica: un movimiento no debería tener ambos valores > 0
        # pero lo permitimos para flexibilidad
        return v


class MovimientoAsientoCreate(MovimientoAsientoBase):
    pass


class MovimientoAsientoResponse(MovimientoAsientoBase):
    id: str
    asiento_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== ASIENTOS CONTABLES ====================

class AsientoContableBase(BaseModel):
    numero: int = Field(..., gt=0)
    codigo_asiento: Optional[str] = Field(None, max_length=50)
    fecha: datetime
    periodo_id: str
    descripcion: str = Field(..., min_length=1)
    tipo_asiento: str = Field(default="manual", max_length=50)
    estado: EstadoAsientoEnum = EstadoAsientoEnum.BORRADOR
    referencia_externa: Optional[str] = Field(None, max_length=100)
    moneda: str = Field(default="USD", max_length=3)
    tasa_cambio: Decimal = Field(default=1.0, ge=0)


class AsientoContableCreate(AsientoContableBase):
    movimientos: List[MovimientoAsientoCreate] = Field(..., min_items=2)
    
    @validator('movimientos')
    def validate_cuadre(cls, v):
        total_debito = sum(m.debito for m in v)
        total_credito = sum(m.credito for m in v)
        if total_debito != total_credito:
            raise ValueError(f'El asiento no cuadra. Débito: {total_debito}, Crédito: {total_credito}')
        return v


class AsientoContableUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoAsientoEnum] = None
    referencia_externa: Optional[str] = None


class AsientoContableResponse(AsientoContableBase):
    id: str
    tenant_id: str
    estado: str
    es_real: bool
    total_debito: Decimal
    total_credito: Decimal
    origen: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    creado_por: Optional[str] = None
    registrado_por: Optional[str] = None
    registrado_en: Optional[datetime] = None
    movimientos: List[MovimientoAsientoResponse] = []
    
    class Config:
        from_attributes = True


# ==================== FILTROS Y BÚSQUEDA ====================

class FiltroCuentasContables(BaseModel):
    tipo_cuenta: Optional[TipoCuentaEnum] = None
    es_activa: Optional[bool] = None
    parent_id: Optional[str] = None
    busca_codigo: Optional[str] = None
    busca_nombre: Optional[str] = None


class FiltroAsientosContables(BaseModel):
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    periodo_id: Optional[str] = None
    estado: Optional[EstadoAsientoEnum] = None
    tipo_asiento: Optional[str] = None
    cuenta_id: Optional[str] = None
    referencia_externa: Optional[str] = None


# ==================== REPORTES ====================

class ReporteBalanceComprobacionItem(BaseModel):
    cuenta_id: str
    codigo: str
    nombre: str
    tipo_cuenta: TipoCuentaEnum
    saldo_inicial_debito: Decimal = 0
    saldo_inicial_credito: Decimal = 0
    movimientos_debito: Decimal = 0
    movimientos_credito: Decimal = 0
    saldo_final_debito: Decimal = 0
    saldo_final_credito: Decimal = 0


class ReporteBalanceComprobacion(BaseModel):
    periodo_id: Optional[str] = None
    fecha_desde: datetime
    fecha_hasta: datetime
    items: List[ReporteBalanceComprobacionItem]
    total_debito: Decimal
    total_credito: Decimal
    cuadra: bool
