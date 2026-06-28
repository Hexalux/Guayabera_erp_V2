from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class DetalleCotizacionBase(BaseModel):
    producto_textil_id: str
    cantidad: int
    precio_unitario: float

class DetalleCotizacionCreate(DetalleCotizacionBase):
    pass

class DetalleCotizacionResponse(DetalleCotizacionBase):
    id: str
    subtotal: float
    producto_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class CotizacionVentaCreate(BaseModel):
    cliente_id: str
    fecha_vigencia: datetime
    notas: Optional[str] = None
    detalles: List[DetalleCotizacionCreate]

class CotizacionVentaResponse(BaseModel):
    id: str
    folio: str
    cliente_id: str
    vendedor_id: str
    fecha_emision: datetime
    fecha_vigencia: datetime
    subtotal: float
    iva: float
    total: float
    estado: str
    notas: Optional[str] = None
    
    cliente_nombre: Optional[str] = None
    vendedor_nombre: Optional[str] = None
    detalles: List[DetalleCotizacionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# ----------------- PEDIDOS -----------------
class DetallePedidoResponse(BaseModel):
    id: str
    producto_textil_id: str
    cantidad_solicitada: int
    cantidad_remisionada: int
    precio_unitario: float
    subtotal: float
    producto_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PedidoVentaResponse(BaseModel):
    id: str
    folio: str
    cotizacion_id: Optional[str] = None
    cliente_id: str
    fecha_pedido: datetime
    fecha_entrega_esperada: Optional[datetime] = None
    subtotal: float
    iva: float
    total: float
    estado: str
    notas: Optional[str] = None
    
    cliente_nombre: Optional[str] = None
    detalles: List[DetallePedidoResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# ----------------- REMISIONES -----------------
class DetalleRemisionResponse(BaseModel):
    id: str
    producto_textil_id: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    producto_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class RemisionVentaResponse(BaseModel):
    id: str
    folio: str
    pedido_id: Optional[str] = None
    cliente_id: str
    fecha_emision: datetime
    subtotal: float
    iva: float
    total: float
    estado: str
    
    cliente_nombre: Optional[str] = None
    cuenta_por_cobrar_id: Optional[str] = None
    poliza_id: Optional[str] = None
    detalles: List[DetalleRemisionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
