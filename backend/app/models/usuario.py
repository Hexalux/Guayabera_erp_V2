from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime  # Importar datetime


class Usuario(Base):
    """
    Modelo para representar un usuario del sistema
    """
    __tablename__ = "usuarios"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()), unique=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    nombre_completo: str = Column(String, nullable=True)
    hashed_password: str = Column(String, nullable=False)
    tipo_usuario: str = Column(String(20), default="normal")  # "normal", "admin_empresa", "superuser"
    is_active: bool = Column(Boolean, default=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'))  # Clave foránea hacia Tenant
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relación con el tenant
    tenant = relationship("Tenant", back_populates="usuarios")

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', nombre_completo='{self.nombre_completo}')>"


# Asegurarse de que uuid4 esté disponible
try:
    from uuid import uuid4
except ImportError:
    from uuid import uuid as uuid4