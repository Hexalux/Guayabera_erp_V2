from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class CuentaBancariaBase(BaseModel):
    banco: str
    numero_cuenta: Optional[str] = None
    clabe: Optional[str] = None
    moneda: str = "MXN"
    cuenta_contable_id: Optional[str] = None

class CuentaBancariaCreate(CuentaBancariaBase):
    pass

class CuentaBancariaResponse(CuentaBancariaBase):
    id: str
    tenant_id: str
    saldo_actual: float
    activa: bool
    
    model_config = ConfigDict(from_attributes=True)

class TransaccionBancariaCreate(BaseModel):
    cuenta_id: str
    monto: float
    referencia: Optional[str] = None
    concepto: str
    metodo_pago: str = "transferencia"
    estado_cheque: Optional[str] = None

class TransaccionBancariaResponse(BaseModel):
    id: str
    tenant_id: str
    cuenta_id: str
    fecha: datetime
    tipo: str
    monto: float
    referencia: Optional[str] = None
    concepto: str
    metodo_pago: str
    estado_cheque: Optional[str] = None
    poliza_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
