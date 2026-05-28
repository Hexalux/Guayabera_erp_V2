from pydantic import BaseModel
from typing import Optional


class GrupoCorporativoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class GrupoCorporativoCreate(GrupoCorporativoBase):
    pass


class GrupoCorporativoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    is_active: Optional[bool] = None


class GrupoCorporativoOut(GrupoCorporativoBase):
    id: str
    is_active: bool

    class Config:
        from_attributes = True


class TenantBase(BaseModel):
    name: str
    subdomain: str
    schema_name: Optional[str] = None
    es_grupo_corporativo: bool = False
    grupo_corporativo_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    descripcion: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    schema_name: Optional[str] = None
    es_grupo_corporativo: Optional[bool] = None
    grupo_corporativo_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    descripcion: Optional[str] = None
    is_active: Optional[bool] = None


class TenantOut(TenantBase):
    id: str
    is_active: bool

    class Config:
        from_attributes = True
