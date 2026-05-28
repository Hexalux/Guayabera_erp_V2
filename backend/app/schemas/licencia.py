from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TipoLicenciaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    duracion_dias: int
    precio: Optional[float] = None
    es_prueba: bool = False


class TipoLicenciaCreate(TipoLicenciaBase):
    pass


class TipoLicenciaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_dias: Optional[int] = None
    precio: Optional[float] = None
    es_prueba: Optional[bool] = None


class TipoLicenciaOut(TipoLicenciaBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LicenciaBase(BaseModel):
    tenant_id: str
    tipo_licencia_id: str
    codigo: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    activa: bool = True
    usada: bool = False
    notas: Optional[str] = None


class LicenciaCreate(LicenciaBase):
    pass


class LicenciaUpdate(BaseModel):
    tenant_id: Optional[str] = None
    tipo_licencia_id: Optional[str] = None
    codigo: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    activa: Optional[bool] = None
    usada: Optional[bool] = None
    notas: Optional[str] = None


class LicenciaOut(LicenciaBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompraLicenciaRequest(BaseModel):
    tenant_id: str
    tipo_licencia_id: str
    cantidad: int = 1  # Para permitir múltiples licencias
