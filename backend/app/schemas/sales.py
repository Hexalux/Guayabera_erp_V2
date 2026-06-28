from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# ==========================================
# CLIENTES
# ==========================================
class ClienteBase(BaseModel):
    razon_social: str
    rfc: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    limite_credito: float = 0.0

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: str
    tenant_id: str
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# ORDENES DE VENTA (COTIZACIONES Y PEDIDOS)
# ==========================================
class DetalleOrdenVentaBase(BaseModel):
    producto_textil_id: str
    cantidad: float
    precio_unitario: float
    descuento_porcentaje: float = 0.0

class DetalleOrdenVentaCreate(DetalleOrdenVentaBase):
    pass

class DetalleOrdenVentaResponse(DetalleOrdenVentaBase):
    id: str
    orden_id: str
    subtotal: float
    
    model_config = ConfigDict(from_attributes=True)

class OrdenVentaBase(BaseModel):
    folio: Optional[str] = None
    fecha_validez: Optional[datetime] = None
    cliente_id: str
    vendedor_id: Optional[str] = None
    estado: str = "borrador"
    notas: Optional[str] = None
    terminos_pago: Optional[str] = None

class OrdenVentaCreate(OrdenVentaBase):
    detalles: List[DetalleOrdenVentaCreate]

class OrdenVentaResponse(OrdenVentaBase):
    id: str
    tenant_id: str
    fecha_emision: datetime
    subtotal: float
    iva: float
    total: float
    detalles: List[DetalleOrdenVentaResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# VENTAS POS
# ==========================================
class DetalleVentaPOSCreate(BaseModel):
    lote_id: str
    cantidad: float
    precio_unitario: float

class DetalleVentaPOSResponse(BaseModel):
    id: str
    lote_id: str
    cantidad: float
    precio_unitario: float
    subtotal: float
    
    model_config = ConfigDict(from_attributes=True)

class VentaPOSCreate(BaseModel):
    cliente_id: Optional[str] = None
    metodo_pago: str = Field(..., pattern="^(EFECTIVO|TARJETA|TRANSFERENCIA)$")
    notas: Optional[str] = None
    detalles: List[DetalleVentaPOSCreate]

class VentaPOSResponse(BaseModel):
    id: UUID
    folio: str
    fecha: datetime
    cliente_id: Optional[str] = None
    vendedor_id: str
    sesion_id: Optional[str] = None
    subtotal: float
    iva: float
    total: float
    metodo_pago: str
    estado: str
    notas: Optional[str] = None
    detalles: List[DetalleVentaPOSResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SESIONES DE CAJA
# ==========================================
class SesionCajaBase(BaseModel):
    fondo_inicial: float = 0.0
    notas: Optional[str] = None

class SesionCajaCreate(SesionCajaBase):
    pass

class SesionCajaClose(BaseModel):
    total_efectivo: float
    total_tarjeta: float
    notas: Optional[str] = None

class SesionCajaResponse(SesionCajaBase):
    id: str
    tenant_id: str
    cajero_id: str
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    total_efectivo: float
    total_tarjeta: float
    diferencia: float
    estado: str
    
    model_config = ConfigDict(from_attributes=True)
