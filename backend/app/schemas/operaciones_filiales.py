from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class TipoOperacion(str, Enum):
    CONSIGNA = "consigna"
    COMPRA = "compra"
    VENTA = "venta"
    APARTADO = "apartado"
    PRESTAMO = "prestamo"
    TRASPASO = "traspaso"
    OTRO = "otro"


class OperacionFilialBase(BaseModel):
    tipo_operacion: TipoOperacion
    tenant_origen_id: str
    tenant_destino_id: str
    descripcion: str
    monto: float = 0.0


class OperacionFilialCreate(OperacionFilialBase):
    fecha_operacion: Optional[datetime] = None


class OperacionFilialUpdate(BaseModel):
    descripcion: Optional[str] = None
    monto: Optional[float] = None
    estado: Optional[str] = None


class OperacionFilialOut(OperacionFilialBase):
    id: str
    fecha_operacion: datetime
    estado: str = "pendiente"

    class Config:
        from_attributes = True