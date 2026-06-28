from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CuentaPorCobrarResponse(BaseModel):
    id: str
    venta_id: str
    cliente_id: str
    cliente_nombre: Optional[str] = None
    folio_venta: Optional[str] = None
    monto_original: float
    saldo_pendiente: float
    fecha_emision: datetime
    fecha_vencimiento: datetime
    estado: str
    
    model_config = ConfigDict(from_attributes=True)

class PagoCxCCreate(BaseModel):
    cuenta_por_cobrar_id: str
    cuenta_bancaria_id: str
    monto: float
    referencia: Optional[str] = None

class PagoCxCResponse(BaseModel):
    id: str
    cuenta_por_cobrar_id: str
    transaccion_bancaria_id: str
    monto: float
    fecha: datetime
    referencia: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class NotaCreditoClienteCreate(BaseModel):
    cuenta_por_cobrar_id: str
    monto: float
    concepto: str

class NotaCreditoClienteResponse(BaseModel):
    id: str
    folio: str
    cuenta_por_cobrar_id: str
    monto: float
    fecha: datetime
    concepto: str
    poliza_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
