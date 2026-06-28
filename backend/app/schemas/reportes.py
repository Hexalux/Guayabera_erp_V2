"""
Schemas para Reportes Financieros y Contables
Validación de parámetros y respuestas de reportes
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class TipoReporte(str, Enum):
    BALANCE_COMPROBACION = "balance_comprobacion"
    BALANCE_GENERAL = "balance_general"
    ESTADO_RESULTADOS = "estado_resultados"
    LIBRO_MAYOR = "libro_mayor"
    LIBRO_DIARIO = "libro_diario"
    ANTIGUEDAD_SALDOS = "antiguedad_saldos"
    FLUJO_EFECTIVO = "flujo_efectivo"


class FiltroFechaBase(BaseModel):
    """Filtro base con fechas"""
    fecha_inicio: date = Field(..., description="Fecha de inicio del período")
    fecha_fin: date = Field(..., description="Fecha de fin del período")
    
    @field_validator('fecha_fin')
    @classmethod
    def validar_fechas(cls, v, info):
        if 'fecha_inicio' in info.data and v < info.data['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class RequestBalanceComprobacion(FiltroFechaBase):
    """Parámetros para Balance de Comprobación"""
    cuenta_id: Optional[int] = Field(None, description="Filtrar por cuenta específica")
    nivel: Optional[int] = Field(None, ge=1, le=10, description="Nivel máximo de cuentas")
    incluir_cero: bool = Field(False, description="Incluir cuentas sin movimientos")


class RequestBalanceGeneral(BaseModel):
    """Parámetros para Balance General"""
    fecha_corte: date = Field(..., description="Fecha de corte del balance")
    comparar_anterior: bool = Field(False, description="Comparar con ejercicio anterior")
    mostrar_detalle: bool = Field(True, description="Mostrar detalle de cuentas")


class RequestEstadoResultados(FiltroFechaBase):
    """Parámetros para Estado de Resultados"""
    centro_costo_id: Optional[int] = Field(None, description="Filtrar por centro de costo")
    mostrar_porcentajes: bool = Field(True, description="Mostrar porcentajes sobre ventas")
    mostrar_margenes: bool = Field(True, description="Mostrar márgenes de utilidad")


class RequestLibroMayor(BaseModel):
    """Parámetros para Libro Mayor"""
    cuenta_id: int = Field(..., description="ID de la cuenta")
    fecha_inicio: date
    fecha_fin: date
    incluir_saldo_inicial: bool = Field(True, description="Incluir saldo inicial")
    
    @field_validator('fecha_fin')
    @classmethod
    def validar_fechas(cls, v, info):
        if 'fecha_inicio' in info.data and v < info.data['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class RequestAntiguedadSaldos(BaseModel):
    """Parámetros para Antigüedad de Saldos"""
    tipo: str = Field(..., description="'clientes' o 'proveedores'")
    fecha_corte: date = Field(..., description="Fecha de corte para antigüedad")
    
    @field_validator('tipo')
    @classmethod
    def validar_tipo(cls, v):
        if v not in ['clientes', 'proveedores']:
            raise ValueError("El tipo debe ser 'clientes' o 'proveedores'")
        return v


class RequestFlujoEfectivo(FiltroFechaBase):
    """Parámetros para Flujo de Efectivo"""
    metodo: str = Field('indirecto', description="'directo' o 'indirecto'")
    mostrar_detalle: bool = Field(True, description="Mostrar detalle de conceptos")


# Schemas de respuesta

class CuentaResumen(BaseModel):
    """Resumen de cuenta para reportes"""
    codigo: str
    nombre: str
    nivel: Optional[int] = None
    tipo: Optional[str] = None
    naturaleza: Optional[str] = None
    saldo: float = 0.0


class MovimientoResumen(BaseModel):
    """Movimiento para libros contables"""
    fecha: date
    numero_asiento: str
    descripcion: str
    referencia: Optional[str] = None
    debe: float = 0.0
    haber: float = 0.0
    saldo: float = 0.0
    centro_costo: Optional[str] = None


class ResponseBalanceComprobacion(BaseModel):
    """Respuesta de Balance de Comprobación"""
    reporte: str
    fecha_inicio: date
    fecha_fin: date
    fecha_generacion: datetime
    cuentas: List[Dict[str, Any]]
    totales: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ResponseBalanceGeneral(BaseModel):
    """Respuesta de Balance General"""
    reporte: str
    fecha_corte: date
    fecha_generacion: datetime
    activos: Dict[str, Any]
    pasivos: Dict[str, Any]
    patrimonio: Dict[str, Any]
    total_activo: float
    total_pasivo_patrimonio: float
    cuadrado: bool
    
    class Config:
        from_attributes = True


class ResponseEstadoResultados(BaseModel):
    """Respuesta de Estado de Resultados"""
    reporte: str
    periodo: Dict[str, date]
    fecha_generacion: datetime
    ingresos: Dict[str, Any]
    costos_ventas: Dict[str, Any]
    utilidad_bruta: float
    gastos_operacion: Dict[str, Any]
    utilidad_operativa: float
    otros_ingresos_gastos: Dict[str, Any]
    utilidad_antes_impuestos: float
    impuestos: Dict[str, Any]
    utilidad_neta: float
    margen_bruto: float
    margen_operativo: float
    margen_netto: float
    
    class Config:
        from_attributes = True


class ResponseLibroMayor(BaseModel):
    """Respuesta de Libro Mayor"""
    reporte: str
    cuenta: Dict[str, Any]
    periodo: Dict[str, date]
    fecha_generacion: datetime
    saldo_inicial: float
    movimientos: List[MovimientoResumen]
    saldo_final: float
    total_movimientos: int
    
    class Config:
        from_attributes = True


class DocumentoAntiguedad(BaseModel):
    """Documento en reporte de antigüedad"""
    folio: str
    tercero: str
    fecha_emision: date
    fecha_vencimiento: date
    dias_vencido: int
    saldo: float
    moneda: str


class ResponseAntiguedadSaldos(BaseModel):
    """Respuesta de Antigüedad de Saldos"""
    reporte: str
    fecha_corte: date
    fecha_generacion: datetime
    rangos: Dict[str, Dict[str, Any]]
    total_general: float
    
    class Config:
        from_attributes = True


class ConceptoFlujo(BaseModel):
    """Concepto en Flujo de Efectivo"""
    concepto: str
    monto: float


class ResponseFlujoEfectivo(BaseModel):
    """Respuesta de Flujo de Efectivo"""
    reporte: str
    metodo: str
    periodo: Dict[str, date]
    fecha_generacion: datetime
    actividades_operacion: Dict[str, Any]
    actividades_inversion: Dict[str, Any]
    actividades_financiamiento: Dict[str, Any]
    incremento_disminucion: float
    efectivo_inicio: float
    efectivo_fin: float
    
    class Config:
        from_attributes = True


# Schema unificado para cualquier reporte
class ResponseReporteGenerico(BaseModel):
    """Respuesta genérica para cualquier reporte"""
    tipo: str
    datos: Dict[str, Any]
    metadata: Dict[str, Any]
    fecha_generacion: datetime
    
    class Config:
        from_attributes = True
