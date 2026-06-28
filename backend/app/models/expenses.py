from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class CategoriaGasto(Base):
    __tablename__ = "categorias_gasto"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)

class GastoOperativo(Base):
    __tablename__ = "gastos_operativos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    categoria_id = Column(String, ForeignKey("categorias_gasto.id"), nullable=False)
    transaccion_bancaria_id = Column(String, ForeignKey("transacciones_bancarias.id"), nullable=True)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False) # Quien registró/comprobó
    
    concepto = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    estado = Column(String, default="pendiente") # pendiente, aprobado, pagado, rechazado
    comprobante_url = Column(String, nullable=True)
    
    categoria = relationship("CategoriaGasto")
    transaccion = relationship("TransaccionBancaria")
    usuario = relationship("Usuario")
