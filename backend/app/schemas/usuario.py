from pydantic import BaseModel
from typing import Optional


class UsuarioBase(BaseModel):
    email: str
    nombre_completo: Optional[str] = None
    tipo_usuario: Optional[str] = 'normal'
    tenant_id: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    tipo_usuario: Optional[str] = None
    tenant_id: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UsuarioOut(UsuarioBase):
    id: str
    is_active: bool

    class Config:
        from_attributes = True