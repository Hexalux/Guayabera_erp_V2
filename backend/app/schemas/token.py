from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TokenVerificacionBase(BaseModel):
    tipo_token: str  # "registro", "recuperacion", "activacion"
    token: str
    expira_en: datetime


class TokenVerificacionCreate(TokenVerificacionBase):
    usuario_id: Optional[str] = None
    admin_id: Optional[str] = None
    tenant_id: Optional[str] = None
    destinatario_email: Optional[str] = None
    nombre_completo: Optional[str] = None


class TokenVerificacionOut(TokenVerificacionBase):
    id: str
    usado: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class SolicitudRegistro(BaseModel):
    email: str
    nombre_completo: Optional[str] = None


class SolicitudRecuperacion(BaseModel):
    email: str


class ConfirmacionToken(BaseModel):
    token: Optional[str] = None
    nueva_contrasena: Optional[str] = None  # Solo para recuperación de contraseña
