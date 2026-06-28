from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime  # Importar datetime


class GrupoCorporativo(Base):
    """
    Modelo para representar un grupo corporativo que puede contener varias empresas filiales
    """
    __tablename__ = "grupos_corporativos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String, nullable=False, index=True)  # Nombre del grupo corporativo
    descripcion: str = Column(Text, nullable=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Tenant(Base):
    """
    Modelo para representar un tenant (empresa/cliente) en el sistema multitenant
    """
    __tablename__ = "tenants"

    # Usamos UUID como identificador único para cada tenant
    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str = Column(String, nullable=False, index=True)  # Nombre de la empresa
    subdomain: str = Column(String, unique=True, nullable=False, index=True)  # Subdominio para acceso
    schema_name: str = Column(String, unique=True, nullable=False)  # Nombre del esquema en la BD
    contact_email: str = Column(String, nullable=True)  # Email de contacto
    descripcion: str = Column(Text, nullable=True)
    
    # Relación con usuarios
    usuarios = relationship("Usuario", order_by="Usuario.id", back_populates="tenant")
    
    # Relación con licencias
    licencias = relationship("Licencia", order_by="Licencia.id", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}')>"

# Alias for backwards compatibility
TenantCorporation = GrupoCorporativo
