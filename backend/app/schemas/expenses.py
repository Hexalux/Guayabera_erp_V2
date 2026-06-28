from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CategoriaGastoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaGastoCreate(CategoriaGastoBase):
    pass

class CategoriaGastoResponse(CategoriaGastoBase):
    id: str
    tenant_id: str
    
    model_config = ConfigDict(from_attributes=True)

class GastoOperativoBase(BaseModel):
    categoria_id: str
    concepto: str
    monto: float
    comprobante_url: Optional[str] = None

class GastoOperativoCreate(GastoOperativoBase):
    pass

class GastoOperativoPay(BaseModel):
    cuenta_bancaria_id: str

class GastoOperativoResponse(GastoOperativoBase):
    id: str
    tenant_id: str
    transaccion_bancaria_id: Optional[str] = None
    usuario_id: str
    fecha: datetime
    estado: str
    
    categoria_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    banco_origen: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
