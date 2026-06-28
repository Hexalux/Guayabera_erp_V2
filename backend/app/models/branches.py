from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Sucursal(Base):
    """Sucursales de la empresa"""
    __tablename__ = "pos_sucursales"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(100), nullable=False)
    codigo: str = Column(String(20), unique=True, nullable=False, index=True)
    direccion: str = Column(Text, nullable=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cajas = relationship("CajaRegistradora", back_populates="sucursal")


class CajaRegistradora(Base):
    """Cajas registradoras (puntos de venta)"""
    __tablename__ = "pos_cajas"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    sucursal_id: str = Column(String, ForeignKey("pos_sucursales.id"), nullable=False)
    nombre: str = Column(String(100), nullable=False)
    codigo: str = Column(String(20), unique=True, nullable=False, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sucursal = relationship("Sucursal", back_populates="cajas")
