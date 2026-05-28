from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime  # Importar datetime
import uuid


class Admin(Base):
    """
    Modelo para representar un superusuario del sistema
    No está asociado a ningún tenant específico
    """
    __tablename__ = "admins"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    nombre_completo: str = Column(String, nullable=True)
    hashed_password: str = Column(String, nullable=False)
    is_verified: bool = Column(Boolean, default=False)  # Si el superusuario ha sido verificado
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Admin(id={self.id}, email='{self.email}', nombre_completo='{self.nombre_completo}')>"
