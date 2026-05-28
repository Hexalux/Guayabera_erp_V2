from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime  # Importar datetime


class TipoLicencia(Base):
    """
    Modelo para representar los tipos de licencia disponibles
    """
    __tablename__ = "tipos_licencia"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String, nullable=False, index=True)  # Ej: "Mensual", "6 Meses", "Anual", "Prueba"
    descripcion: str = Column(Text, nullable=True)
    duracion_dias: int = Column(Integer, nullable=False)  # Duración en días
    precio: float = Column(Float, nullable=True)  # Precio en caso de ser de paga
    es_prueba: bool = Column(Boolean, default=False)  # Indica si es una licencia de prueba
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relaciones
    licencias_asignadas = relationship("Licencia", back_populates="tipo_licencia")


class Licencia(Base):
    """
    Modelo para representar una licencia asignada a un tenant
    """
    __tablename__ = "licencias"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=False)  # Tenant al que pertenece
    tipo_licencia_id: str = Column(String, ForeignKey('tipos_licencia.id'), nullable=False)  # Tipo de licencia
    codigo: str = Column(String, unique=True, nullable=False, index=True)  # Código único de la licencia
    fecha_inicio: datetime = Column(DateTime(timezone=True), server_default=func.now())  # Fecha de inicio
    fecha_fin: datetime = Column(DateTime(timezone=True), nullable=False)  # Fecha de finalización
    activa: bool = Column(Boolean, default=True)  # Indica si la licencia está activa
    usada: bool = Column(Boolean, default=False)  # Indica si la licencia ha sido utilizada (para claves de activación)
    notas: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relaciones
    tenant = relationship("Tenant", back_populates="licencias")
    tipo_licencia = relationship("TipoLicencia", back_populates="licencias_asignadas")