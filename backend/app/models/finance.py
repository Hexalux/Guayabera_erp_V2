from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class CuentaContable(Base):
    """Plan de Cuentas - Estructura tipo CONTPAQi"""
    __tablename__ = "cont_cuentas"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    codigo: str = Column(String(50), unique=True, nullable=False, index=True)  # Ej. "101.01.001"
    nombre: str = Column(String(200), nullable=False)
    nivel: int = Column(Integer, nullable=False, default=1)  # 1, 2, 3, 4
    tipo: str = Column(String(50), nullable=False)  # "activo", "pasivo", "capital", "ingresos", "costos", "gastos"
    naturaleza: str = Column(String(20), default="deudora")  # "deudora", "acreedora"
    es_agrupadora: bool = Column(Boolean, default=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    cuenta_padre_id: str = Column(String, ForeignKey("cont_cuentas.id"), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    cuenta_padre = relationship("CuentaContable", remote_side=[id], backref="cuentas_hijas")
    movimientos = relationship("MovimientoPoliza", back_populates="cuenta")


class PolizaContable(Base):
    """Pólizas Contables (Ingresos, Egresos, Diario)"""
    __tablename__ = "cont_polizas"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    numero: int = Column(Integer, nullable=False, index=True)
    tipo: str = Column(String(50), nullable=False)  # "ingreso", "egreso", "diario"
    fecha = Column(Date, nullable=False)
    descripcion: str = Column(Text, nullable=False)
    estado: str = Column(String(20), default="borrador")  # "borrador", "aprobada", "cancelada"
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    total_cargos: float = Column(Numeric(15, 2), default=0.00)
    total_abonos: float = Column(Numeric(15, 2), default=0.00)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    movimientos = relationship("MovimientoPoliza", back_populates="poliza", cascade="all, delete-orphan")


class MovimientoPoliza(Base):
    """Partidas de pólizas contables"""
    __tablename__ = "cont_movimientos_poliza"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    poliza_id: str = Column(String, ForeignKey("cont_polizas.id"), nullable=False)
    cuenta_id: str = Column(String, ForeignKey("cont_cuentas.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    cargo: float = Column(Numeric(15, 2), default=0.00)
    abono: float = Column(Numeric(15, 2), default=0.00)
    concepto: str = Column(String(500), nullable=False)
    referencia: str = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    poliza = relationship("PolizaContable", back_populates="movimientos")
    cuenta = relationship("CuentaContable", back_populates="movimientos")


class Banco(Base):
    """Cuentas bancarias de la empresa"""
    __tablename__ = "cont_bancos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(100), nullable=False)
    cuenta: str = Column(String(50), nullable=False)
    clabe: str = Column(String(18), nullable=True)
    moneda: str = Column(String(3), default="MXN")
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    cuenta_contable_id: str = Column(String, ForeignKey("cont_cuentas.id"), nullable=True)
    saldo_actual: float = Column(Numeric(15, 2), default=0.00)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cuenta_contable = relationship("CuentaContable")
    movimientos_bancarios = relationship("MovimientoBancario", back_populates="banco")


class MovimientoBancario(Base):
    """Transacciones bancarias para conciliación"""
    __tablename__ = "cont_movimientos_bancarios"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    banco_id: str = Column(String, ForeignKey("cont_bancos.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    fecha = Column(Date, nullable=False)
    descripcion: str = Column(String(500), nullable=False)
    referencia: str = Column(String(50), nullable=True)
    cargo: float = Column(Numeric(15, 2), default=0.00)
    abono: float = Column(Numeric(15, 2), default=0.00)
    conciliado: bool = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    banco = relationship("Banco", back_populates="movimientos_bancarios")
