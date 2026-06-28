from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class CuentaBancaria(Base):
    __tablename__ = "cuentas_bancarias"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    banco = Column(String, nullable=False) # ej. Banorte, Santander, Caja General
    numero_cuenta = Column(String, nullable=True)
    clabe = Column(String, nullable=True)
    moneda = Column(String, default="MXN")
    
    saldo_actual = Column(Float, default=0.0, nullable=False)
    cuenta_contable_id = Column(String, ForeignKey("cont_cuentas.id"), nullable=True)
    
    activa = Column(Boolean, default=True)
    
    transacciones = relationship("TransaccionBancaria", back_populates="cuenta")

class TransaccionBancaria(Base):
    __tablename__ = "transacciones_bancarias"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    cuenta_id = Column(String, ForeignKey("cuentas_bancarias.id"), nullable=False)
    
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    tipo = Column(String, nullable=False) # ingreso, egreso
    monto = Column(Float, nullable=False)
    
    referencia = Column(String, nullable=True)
    concepto = Column(Text, nullable=False)
    
    # Nuevos campos para Sprint 7: Tesorería y Cheques
    metodo_pago = Column(String, default="transferencia", nullable=False) # efectivo, transferencia, cheque, tarjeta
    estado_cheque = Column(String, nullable=True) # emitido, cobrado, rebotado (solo si metodo_pago == 'cheque')
    
    poliza_id = Column(String, ForeignKey("cont_polizas.id"), nullable=True)
    
    cuenta = relationship("CuentaBancaria", back_populates="transacciones")
