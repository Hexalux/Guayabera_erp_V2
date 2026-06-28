from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone, timedelta

from app.core.database import Base

class CuentaPorCobrar(Base):
    __tablename__ = "cuentas_por_cobrar"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    venta_id = Column(String, ForeignKey("ventas_pos.id"), nullable=False)
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    
    monto_original = Column(Float, nullable=False)
    saldo_pendiente = Column(Float, nullable=False)
    
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    
    estado = Column(String, default="vigente") # vigente, vencida, pagada
    
    venta = relationship("VentaPOS")
    cliente = relationship("Cliente")
    pagos = relationship("PagoCxC", back_populates="cuenta_por_cobrar")
    notas_credito = relationship("NotaCreditoCliente", back_populates="cuenta_por_cobrar")

class PagoCxC(Base):
    __tablename__ = "pagos_cxc"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    cuenta_por_cobrar_id = Column(String, ForeignKey("cuentas_por_cobrar.id"), nullable=False)
    transaccion_bancaria_id = Column(String, ForeignKey("transacciones_bancarias.id"), nullable=True) # El ingreso en banco
    
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    referencia = Column(String, nullable=True)
    
    cuenta_por_cobrar = relationship("CuentaPorCobrar", back_populates="pagos")
    transaccion = relationship("TransaccionBancaria")

class NotaCreditoCliente(Base):
    __tablename__ = "notas_credito_cliente"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    folio = Column(String, index=True, unique=True, nullable=False)
    cuenta_por_cobrar_id = Column(String, ForeignKey("cuentas_por_cobrar.id"), nullable=False)
    
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    concepto = Column(Text, nullable=False)
    
    poliza_id = Column(String, ForeignKey("cont_polizas.id"), nullable=True)
    
    cuenta_por_cobrar = relationship("CuentaPorCobrar", back_populates="notas_credito")
