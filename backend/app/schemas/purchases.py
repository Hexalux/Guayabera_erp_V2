from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# ==========================================
# PROVEEDORES
# ==========================================
class ProveedorBase(BaseModel):
    razon_social: str
    rfc: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    dias_credito: float = 0.0

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorResponse(ProveedorBase):
    id: UUID
    tenant_id: str
    activo: bool
    
    model_config = ConfigDict(from_attributes=True)

class ListaPrecioProveedorBase(BaseModel):
    producto_textil_id: str
    codigo_proveedor: Optional[str] = None
    precio: float
    moneda: str = "MXN"
    factor_conversion: float = 1.0

class ListaPrecioProveedorCreate(ListaPrecioProveedorBase):
    proveedor_id: str

class ListaPrecioProveedorResponse(ListaPrecioProveedorBase):
    id: UUID
    proveedor_id: UUID
    tenant_id: str
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# ORDENES DE COMPRA
# ==========================================
class DetalleOrdenCompraCreate(BaseModel):
    producto_textil_id: str
    cantidad_solicitada: float
    precio_unitario: float

class DetalleOrdenCompraResponse(BaseModel):
    id: UUID
    producto_textil_id: UUID
    cantidad_solicitada: float
    cantidad_recibida: float
    precio_unitario: float
    subtotal: float
    
    model_config = ConfigDict(from_attributes=True)

class OrdenCompraCreate(BaseModel):
    proveedor_id: str
    notas: Optional[str] = None
    detalles: List[DetalleOrdenCompraCreate]

class OrdenCompraResponse(BaseModel):
    id: UUID
    folio: str
    fecha_emision: datetime
    fecha_recepcion: Optional[datetime] = None
    proveedor_id: UUID
    comprador_id: UUID
    estado: str
    subtotal: float
    iva: float
    total: float
    notas: Optional[str] = None
    detalles: List[DetalleOrdenCompraResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# CUENTAS POR PAGAR (CXP)
# ==========================================
class CuentaPorPagarResponse(BaseModel):
    id: str
    tenant_id: str
    orden_compra_id: str
    proveedor_id: str
    monto_original: float
    monto_pagado: float
    saldo_pendiente: float
    fecha_emision: datetime
    fecha_vencimiento: datetime
    estado: str
    
    # Adicionales para frontend
    proveedor_nombre: Optional[str] = None
    folio_orden: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PagoCxPCreate(BaseModel):
    cuenta_por_pagar_id: str
    cuenta_bancaria_id: str
    monto: float
    referencia: Optional[str] = None

class PagoCxPResponse(BaseModel):
    id: str
    cuenta_por_pagar_id: str
    transaccion_bancaria_id: str
    monto: float
    fecha: datetime
    referencia: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
