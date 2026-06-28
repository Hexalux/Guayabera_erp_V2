"""
Esquemas Pydantic para Cuentas por Cobrar (CXC)
Fusión de CONTPAQi (robustez), Odoo (flexibilidad), Management Pro (opciones)
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal


class TipoDocumentoCXC(str, Enum):
    FACTURA = "factura"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    RECIBO = "recibo"
    PAGARE = "pagare"
    ANTICIPO = "anticipo"
    COBRO = "cobro"
    INTERES_MORATORIO = "interes_moratorio"


class EstadoDocumentoCXC(str, Enum):
    BORRADOR = "borrador"
    REGISTRADO = "registrado"
    PARCIAL = "parcial"
    SALDADO = "saldado"
    VENCIDO = "vencido"
    CANCELADO = "cancelado"
    COBRANZA = "cobranza"


class FormaPago(str, Enum):
    CONTADO = "contado"
    CREDITO = "credito"
    PARCIAL = "parcial"


# ==================== SCHEMAS BASE ====================

class DocumentoCXCBase(BaseModel):
    tipo_documento: TipoDocumentoCXC
    cliente_id: UUID
    fecha_emision: date
    fecha_vencimiento: date
    forma_pago: FormaPago = FormaPago.CREDITO
    dias_plazo: int = Field(default=0, ge=0, le=365)
    
    # Valores monetarios
    subtotal: Decimal = Field(default=0, ge=0)
    descuento: Decimal = Field(default=0, ge=0)
    iva: Decimal = Field(default=0, ge=0)
    ice: Decimal = Field(default=0, ge=0)
    otros_impuestos: Decimal = Field(default=0, ge=0)
    total: Decimal
    
    moneda: str = Field(default="USD", max_length=3)
    tipo_cambio: Decimal = Field(default=1.0, ge=0)
    
    # Contabilización
    cuenta_contable: Optional[str] = Field(None, max_length=20)
    centro_costo_id: Optional[UUID] = None
    
    # Vendedor
    vendedor_id: Optional[UUID] = None
    comision_porcentaje: Decimal = Field(default=0, ge=0, le=100)
    
    observaciones: Optional[str] = None


class DocumentoCXCCreate(DocumentoCXCBase):
    """Schema para crear un nuevo documento CXC"""
    
    @validator('total')
    def validar_total(cls, v, values):
        subtotal = float(values.get('subtotal', 0))
        descuento = float(values.get('descuento', 0))
        iva = float(values.get('iva', 0))
        ice = float(values.get('ice', 0))
        otros = float(values.get('otros_impuestos', 0))
        
        esperado = Decimal(str(subtotal - descuento + iva + ice + otros))
        if abs(v - esperado) > Decimal('0.01'):
            raise ValueError(f'El total ({v}) no coincide con la suma de conceptos ({esperado})')
        return v
    
    @validator('fecha_vencimiento')
    def validar_fechas(cls, v, values):
        if 'fecha_emision' in values and v < values['fecha_emision']:
            raise ValueError('La fecha de vencimiento no puede ser anterior a la fecha de emisión')
        return v


class DocumentoXCUpdate(BaseModel):
    """Schema para actualizar documento CXC (solo campos permitidos)"""
    observaciones: Optional[str] = None
    fecha_limite_pago: Optional[date] = None
    vendedor_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None


class DocumentoXCResponse(DocumentoCXCBase):
    id: UUID
    tenant_id: UUID
    codigo: str
    serie: str
    consecutivo: int
    folio: str
    saldo_pendiente: Decimal
    saldo_vencido: Decimal
    estado: EstadoDocumentoCXC
    es_aplicado: bool
    es_electronico: bool
    clave_acceso_sri: Optional[str] = None
    numero_autorizacion: Optional[str] = None
    asiento_contable_id: Optional[UUID] = None
    
    # Datos del cliente
    cliente_nombre: Optional[str] = None
    cliente_identificacion: Optional[str] = None
    
    # Auditoría
    fecha_creacion: datetime
    usuario_creacion: UUID
    
    class Config:
        from_attributes = True


# ==================== MOVIMIENTOS Y APLICACIONES ====================

class MovimientoCXCCreate(BaseModel):
    documento_id: UUID
    tipo_movimiento: str
    valor_aplicado: Decimal = Field(ge=0)
    observaciones: Optional[str] = None


class MovimientoXCResponse(BaseModel):
    id: UUID
    documento_id: UUID
    tipo_movimiento: str
    fecha_movimiento: datetime
    valor_original: Decimal
    valor_aplicado: Decimal
    saldo_anterior: Decimal
    saldo_nuevo: Decimal
    observaciones: Optional[str] = None
    usuario_creacion: UUID
    
    class Config:
        from_attributes = True


class AplicacionCXCCreate(BaseModel):
    """Aplicar pago/nota crédito a documentos"""
    documento_pago_id: UUID  # El pago o nota de crédito
    documento_aplicado_id: UUID  # La factura u otro documento
    valor_aplicado: Decimal = Field(gt=0)
    tipo_aplicacion: str  # pago, nota_credito, anticipo, bonificacion
    observaciones: Optional[str] = None


class AplicacionXCResponse(BaseModel):
    id: UUID
    documento_pago_id: UUID
    documento_aplicado_id: UUID
    fecha_aplicacion: datetime
    valor_aplicado: Decimal
    tipo_aplicacion: str
    observaciones: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== COBROS Y RELACIONES ====================

class CobroCreate(BaseModel):
    """Registrar un cobro"""
    cliente_id: UUID
    fecha_cobro: date
    forma_pago: str  # efectivo, cheque, transferencia, tarjeta
    referencia_pago: Optional[str] = Field(None, max_length=100)
    banco_id: Optional[UUID] = None
    numero_cheque: Optional[str] = Field(None, max_length=20)
    
    # Valores
    subtotal: Decimal = Field(default=0, ge=0)
    descuento: Decimal = Field(default=0, ge=0)
    iva: Decimal = Field(default=0, ge=0)
    total: Decimal
    
    # Documentos a aplicar
    documentos_a_aplicar: List[Dict[str, Any]] = []  # [{documento_id, valor}]
    
    observaciones: Optional[str] = None


class CobroResponse(BaseModel):
    id: UUID
    codigo: str
    cliente_id: UUID
    cliente_nombre: str
    fecha_cobro: date
    forma_pago: str
    total: Decimal
    total_aplicado: Decimal
    saldo_por_aplicar: Decimal
    estado: str
    observaciones: Optional[str] = None
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


class RelacionCobranzaCreate(BaseModel):
    """Crear relación de cobranza"""
    cliente_id: UUID
    fecha_elaboracion: date
    documentos: List[UUID]  # IDs de documentos a incluir
    observaciones: Optional[str] = None


class RelacionCobranzaResponse(BaseModel):
    id: UUID
    codigo: str
    cliente_id: UUID
    cliente_nombre: str
    fecha_elaboracion: date
    total_documentos: int
    total_valor: Decimal
    estado: str
    recibo_caja_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== NOTAS DE CRÉDITO/DÉBITO ====================

class NotaCreditoCreate(DocumentoCXCBase):
    """Crear nota de crédito directa"""
    tipo_documento: TipoDocumentoCXC = TipoDocumentoCXC.NOTA_CREDITO
    documento_origen_id: Optional[UUID] = None  # Factura original
    motivo: str = Field(..., min_length=10, max_length=500)  # Razón de la NC
    tipo_nota_credito: str  # directa, bonificacion, devolucion, pre_pedido


class NotaDebitoCreate(DocumentoCXCBase):
    """Crear nota de débito"""
    tipo_documento: TipoDocumentoCXC = TipoDocumentoCXC.NOTA_DEBITO
    documento_origen_id: Optional[UUID] = None
    motivo: str = Field(..., min_length=10, max_length=500)


# ==================== ANTICIPOS ====================

class AnticipoCreate(BaseModel):
    """Registrar anticipo de cliente"""
    cliente_id: UUID
    fecha: date
    total: Decimal
    forma_pago: str
    referencia: Optional[str] = None
    observaciones: Optional[str] = None


class AnticipoResponse(BaseModel):
    id: UUID
    codigo: str
    cliente_id: UUID
    cliente_nombre: str
    fecha: date
    total: Decimal
    saldo_pendiente: Decimal
    estado: EstadoDocumentoCXC
    observaciones: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== INTERESES MORATORIOS ====================

class InteresMoratorioCalculation(BaseModel):
    """Calcular intereses moratorios"""
    documento_id: UUID
    fecha_calculo: date
    tasa_interes_anual: Decimal = Field(gt=0, le=100)
    dias_gracia: int = Field(default=0, ge=0)


class InteresMoratorioResponse(BaseModel):
    id: UUID
    documento_id: UUID
    documento_codigo: str
    fecha_calculo: date
    dias_mora: int
    tasa_interes_anual: Decimal
    base_calculo: Decimal
    valor_interes: Decimal
    estado: str
    documento_generado_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# ==================== FILTROS Y REPORTES ====================

class CXCFiltro(BaseModel):
    """Filtros para búsqueda de documentos CXC"""
    tipo_documento: Optional[TipoDocumentoCXC] = None
    cliente_id: Optional[UUID] = None
    estado: Optional[EstadoDocumentoCXC] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    vencido: Optional[bool] = None
    vendedor_id: Optional[UUID] = None


class ResumenCarteraCliente(BaseModel):
    """Resumen de cartera para un cliente"""
    cliente_id: UUID
    cliente_nombre: str
    cliente_identificacion: str
    limite_credito: Optional[Decimal]
    saldo_total: Decimal
    saldo_vencido: Decimal
    saldo_por_vencer: Decimal
    disponible_credito: Optional[Decimal]
    documentos_vencidos_count: int
    ultimo_movimiento: Optional[datetime] = None


class ReporteAntiguedadSaldos(BaseModel):
    """Reporte de antigüedad de saldos"""
    cliente_id: UUID
    cliente_nombre: str
    corriente: Decimal  # 0-30 días
    dias_30_60: Decimal
    dias_60_90: Decimal
    dias_90_120: Decimal
    mas_120: Decimal
    total: Decimal


class EstadoCuentaCliente(BaseModel):
    """Estado de cuenta completo"""
    cliente_id: UUID
    cliente_nombre: str
    cliente_identificacion: str
    fecha_corte: date
    saldo_inicial: Decimal
    movimientos: List[Dict[str, Any]]
    saldo_final: Decimal
    documentos_vencidos: List[Dict[str, Any]]
    documentos_por_vencer: List[Dict[str, Any]]
