from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class TicketSoporte(Base):
    """Tickets de Helpdesk para soporte técnico y atención"""
    __tablename__ = "hd_tickets"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    folio: str = Column(String(50), unique=True, nullable=False, index=True)
    asunto: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=False)
    estado: str = Column(String(50), default="abierto")  # abierto, en_espera, resuelto, cerrado
    prioridad: str = Column(String(50), default="media")  # baja, media, alta, critica
    
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    usuario_creador_id: str = Column(String, ForeignKey("usuarios.id"), nullable=False)
    tecnico_asignado_id: str = Column(String, ForeignKey("usuarios.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    usuario_creador = relationship("Usuario", foreign_keys=[usuario_creador_id])
    tecnico_asignado = relationship("Usuario", foreign_keys=[tecnico_asignado_id])
