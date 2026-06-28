from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date

# -----------------
# CUENTA CONTABLE
# -----------------

class CuentaContableBase(BaseModel):
    codigo: str = Field(..., description="Código de la cuenta, ej. 101.01.001")
    nombre: str = Field(..., description="Nombre de la cuenta")
    nivel: int = Field(1, description="Nivel en el catálogo de cuentas")
    tipo: str = Field(..., description="activo, pasivo, capital, ingresos, costos, gastos")
    naturaleza: str = Field("deudora", description="deudora, acreedora")
    es_agrupadora: bool = Field(False)
    cuenta_padre_id: Optional[str] = None
    is_active: bool = Field(True)

class CuentaContableCreate(CuentaContableBase):
    pass

class CuentaContableUpdate(CuentaContableBase):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    tipo: Optional[str] = None

class CuentaContableOut(CuentaContableBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------
# MOVIMIENTO POLIZA
# -----------------

class MovimientoPolizaBase(BaseModel):
    cuenta_id: str
    cargo: float = Field(0.00, ge=0)
    abono: float = Field(0.00, ge=0)
    concepto: str
    referencia: Optional[str] = None

class MovimientoPolizaCreate(MovimientoPolizaBase):
    pass

class MovimientoPolizaOut(MovimientoPolizaBase):
    id: str
    poliza_id: str
    tenant_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------
# POLIZA CONTABLE
# -----------------

class PolizaContableBase(BaseModel):
    numero: int
    tipo: str = Field(..., description="ingreso, egreso, diario")
    fecha: date
    descripcion: str
    estado: str = Field("borrador", description="borrador, aprobada, cancelada")

class PolizaContableCreate(PolizaContableBase):
    movimientos: List[MovimientoPolizaCreate] = []

    @validator('movimientos')
    def validar_cuadre_poliza(cls, movimientos, values):
        # We only check cuadre strictly if it's not a borrador. But let's check it strictly here if they provide it.
        # However, for 'borrador', it might not be strictly squared.
        estado = values.get('estado', 'borrador')
        total_cargos = sum(m.cargo for m in movimientos)
        total_abonos = sum(m.abono for m in movimientos)
        
        # Using abs due to floating point precision issues
        if estado != 'borrador' and abs(total_cargos - total_abonos) > 0.01:
            raise ValueError(f"La póliza no está cuadrada. Cargos: {total_cargos}, Abonos: {total_abonos}")
        return movimientos

class PolizaContableOut(PolizaContableBase):
    id: str
    tenant_id: Optional[str]
    total_cargos: float
    total_abonos: float
    created_at: datetime
    updated_at: datetime
    movimientos: List[MovimientoPolizaOut] = []

    class Config:
        from_attributes = True


# -----------------
# BANCO
# -----------------

class BancoBase(BaseModel):
    nombre: str
    cuenta: str
    clabe: Optional[str] = None
    moneda: str = "MXN"
    cuenta_contable_id: Optional[str] = None
    saldo_actual: float = 0.00
    is_active: bool = True

class BancoCreate(BancoBase):
    pass

class BancoOut(BancoBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------
# MOVIMIENTO BANCARIO
# -----------------

class MovimientoBancarioBase(BaseModel):
    banco_id: str
    fecha: date
    descripcion: str
    referencia: Optional[str] = None
    cargo: float = 0.00
    abono: float = 0.00
    conciliado: bool = False

class MovimientoBancarioCreate(MovimientoBancarioBase):
    pass

class MovimientoBancarioOut(MovimientoBancarioBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
