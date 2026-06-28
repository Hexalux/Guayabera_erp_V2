from pydantic import BaseModel, Field, validator
from typing import Optional, List, Decimal
from datetime import date, datetime
from enum import Enum

class EstadoFactura(str, Enum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADA = "pagada"
    CANCELADA = "cancelada"

class EstadoPago(str, Enum):
    BORRADOR = "borrador"
    AUTORIZADO = "autorizado"
    PAGADO = "pagado"
    CANCELADO = "cancelado"

# --- Proveedor ---
class ProveedorBase(BaseModel):
    nombre: str
    identificacion_fiscal: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    limite_credito: Decimal = Field(default=0.0, ge=0)
    dias_credito: int = Field(default=0, ge=0)
    activo: bool = True

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    limite_credito: Optional[Decimal] = None
    dias_credito: Optional[int] = None
    activo: Optional[bool] = None

class ProveedorResponse(ProveedorBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Factura Proveedor ---
class FacturaProveedorBase(BaseModel):
    numero_factura: str
    fecha_emision: date
    fecha_vencimiento: date
    subtotal: Decimal
    impuestos: Decimal = Field(default=0.0)
    total: Decimal
    moneda: str = "USD"
    tipo_cambio: Decimal = Field(default=1.0, ge=0)
    centro_costo_id: Optional[int] = None
    descripcion: Optional[str] = None

class FacturaProveedorCreate(FacturaProveedorBase):
    proveedor_id: int

class FacturaProveedorUpdate(BaseModel):
    estado: Optional[EstadoFactura] = None
    descripcion: Optional[str] = None

class FacturaProveedorResponse(FacturaProveedorBase):
    id: int
    proveedor_id: int
    saldo_pendiente: Decimal
    estado: EstadoFactura
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Pago Proveedor ---
class PagoProveedorBase(BaseModel):
    fecha_pago: date
    monto: Decimal
    metodo_pago: str  # Transferencia, Cheque, Efectivo
    referencia: Optional[str] = None
    notas: Optional[str] = None

class PagoProveedorCreate(PagoProveedorBase):
    proveedor_id: int
    facturas_a_pagar: List[int] = []  # IDs de facturas
    es_anticipo: bool = False

class PagoProveedorResponse(PagoProveedorBase):
    id: int
    estado: EstadoPago
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Nota de Crédito ---
class NotaCreditoProveedorBase(BaseModel):
    numero_nota: str
    fecha: date
    monto: Decimal
    motivo: str
    factura_origen_id: Optional[int] = None

class NotaCreditoProveedorCreate(NotaCreditoProveedorBase):
    proveedor_id: int

class NotaCreditoProveedorResponse(NotaCreditoProveedorBase):
    id: int
    proveedor_id: int
    aplicada: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Retención ---
class RetencionProveedorBase(BaseModel):
    tipo_impuesto: str  # ISR, IVA, IEPS
    porcentaje: Decimal
    base_gravable: Decimal
    monto_retencion: Decimal

class RetencionProveedorCreate(RetencionProveedorBase):
    factura_id: int

class RetencionProveedorResponse(RetencionProveedorBase):
    id: int
    factura_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
