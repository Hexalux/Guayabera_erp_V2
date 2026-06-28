from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum


class TipoCuenta(enum.Enum):
    """Tipos de cuentas contables"""
    ACTIVO = "activo"
    PASIVO = "pasivo"
    PATRIMONIO = "patrimonio"
    INGRESO = "ingreso"
    GASTO = "gasto"
    COSTO = "costo"


class NaturalezaCuenta(enum.Enum):
    """Naturaleza de la cuenta (débito o crédito)"""
    DEUDORA = "deudora"
    ACREEDORA = "acreedora"


class CuentaContable(Base):
    """
    Modelo para representar el Plan de Cuentas Contables
    Soporta jerarquía mediante parent_id y multi-moneda
    """
    __tablename__ = "cuentas_contables"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Código y nombre de la cuenta
    codigo: str = Column(String(50), nullable=False, index=True)
    nombre: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=True)
    
    # Jerarquía
    nivel: int = Column(Integer, default=1)
    parent_id: str = Column(String, ForeignKey("cuentas_contables.id"), nullable=True, index=True)
    
    # Clasificación
    tipo_cuenta: TipoCuenta = Column(SQLEnum(TipoCuenta), nullable=False, index=True)
    naturaleza: NaturalezaCuenta = Column(SQLEnum(NaturalezaCuenta), default=NaturalezaCuenta.DEUDORA)
    
    # Configuración
    es_movimiento: bool = Column(Boolean, default=True)  # Si False, es cuenta de grupo/resumen
    es_activa: bool = Column(Boolean, default=True)
    requiere_centro_costo: bool = Column(Boolean, default=False)
    requiere_tercero: bool = Column(Boolean, default=False)
    
    # Multi-moneda
    permite_multimoneda: bool = Column(Boolean, default=False)
    moneda_base: str = Column(String(3), default="USD")
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_by: str = Column(String, nullable=True)
    
    # Relaciones
    parent = relationship("CuentaContable", remote_side=[id], backref="children")
    movimientos = relationship("MovimientoAsiento", back_populates="cuenta")
    tenant = relationship("Tenant", backref="cuentas_contables")

    def __repr__(self):
        return f"<CuentaContable(codigo='{self.codigo}', nombre='{self.nombre}')>"


class CentroCosto(Base):
    """
    Modelo para representar Centros de Costo
    """
    __tablename__ = "centros_costo"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    codigo: str = Column(String(50), nullable=False, index=True)
    nombre: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=True)
    
    es_activo: bool = Column(Boolean, default=True)
    nivel: int = Column(Integer, default=1)
    parent_id: str = Column(String, ForeignKey("centros_costo.id"), nullable=True, index=True)
    
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relaciones
    parent = relationship("CentroCosto", remote_side=[id], backref="children")
    movimientos = relationship("MovimientoAsiento", back_populates="centro_costo")
    tenant = relationship("Tenant", backref="centros_costo")

    def __repr__(self):
        return f"<CentroCosto(codigo='{self.codigo}', nombre='{self.nombre}')>"


class PeriodoContable(Base):
    """
    Modelo para representar Períodos Contables
    Controla qué períodos están abiertos o cerrados para registro
    """
    __tablename__ = "periodos_contables"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    nombre: str = Column(String(100), nullable=False)
    fecha_inicio: datetime = Column(DateTime, nullable=False)
    fecha_fin: datetime = Column(DateTime, nullable=False)
    
    esta_cerrado: bool = Column(Boolean, default=False)
    es_anual: bool = Column(Boolean, default=False)
    
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    cerrado_por: str = Column(String, nullable=True)
    cerrado_en: datetime = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    tenant = relationship("Tenant", backref="periodos_contables")
    asientos = relationship("AsientoContable", back_populates="periodo")

    def __repr__(self):
        return f"<PeriodoContable(nombre='{self.nombre}', cerrado={self.esta_cerrado})>"


class AsientoContable(Base):
    """
    Modelo para representar Asientos Contables
    """
    __tablename__ = "asientos_contables"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Numeración y clasificación
    numero: int = Column(Integer, nullable=False, index=True)
    codigo_asiento: str = Column(String(50), nullable=True, index=True)  # Código legible ej: AS-2024-001
    
    # Fecha y período
    fecha: datetime = Column(DateTime, nullable=False, index=True)
    periodo_id: str = Column(String, ForeignKey("periodos_contables.id"), nullable=False, index=True)
    
    # Descripción y tipo
    descripcion: str = Column(Text, nullable=False)
    tipo_asiento: str = Column(String(50), default="manual")  # manual, automatico, ajuste, cierre, apertura
    
    # Estado
    estado: str = Column(String(20), default="borrador")  # borrador, registrado, anulado
    es_real: bool = Column(Boolean, default=True)  # True=real, False=reverso/ajuste
    
    # Totales
    total_debito: Numeric = Column(Numeric(19, 4), default=0)
    total_credito: Numeric = Column(Numeric(19, 4), default=0)
    moneda: str = Column(String(3), default="USD")
    tasa_cambio: Numeric = Column(Numeric(19, 6), default=1.0)
    
    # Referencias externas
    referencia_externa: str = Column(String(100), nullable=True)  # Número factura, documento, etc.
    origen: str = Column(String(50), nullable=True)  # modulo que generó el asiento
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    creado_por: str = Column(String, nullable=True)
    registrado_por: str = Column(String, nullable=True)
    registrado_en: datetime = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    periodo = relationship("PeriodoContable", back_populates="asientos")
    movimientos = relationship("MovimientoAsiento", back_populates="asiento", cascade="all, delete-orphan")
    tenant = relationship("Tenant", backref="asientos_contables")

    def __repr__(self):
        return f"<AsientoContable(numero={self.numero}, fecha={self.fecha})>"


class MovimientoAsiento(Base):
    """
    Modelo para representar las partidas/movimientos de un Asiento Contable
    """
    __tablename__ = "movimientos_asiento"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    asiento_id: str = Column(String, ForeignKey("asientos_contables.id", ondelete="CASCADE"), nullable=False, index=True)
    cuenta_id: str = Column(String, ForeignKey("cuentas_contables.id"), nullable=False, index=True)
    
    # Valores
    debito: Numeric = Column(Numeric(19, 4), default=0)
    credito: Numeric = Column(Numeric(19, 4), default=0)
    
    # Centro de costo (opcional)
    centro_costo_id: str = Column(String, ForeignKey("centros_costo.id"), nullable=True, index=True)
    
    # Tercero (opcional) - se implementará en Sprint 2
    tercero_id: str = Column(String, nullable=True, index=True)
    tipo_tercero: str = Column(String(20), nullable=True)  # cliente, proveedor, empleado, otro
    
    # Descripción específica del movimiento
    descripcion: str = Column(Text, nullable=True)
    
    # Multi-moneda
    moneda: str = Column(String(3), default="USD")
    tasa_cambio: Numeric = Column(Numeric(19, 6), default=1.0)
    valor_original: Numeric = Column(Numeric(19, 4), nullable=True)
    
    # Orden dentro del asiento
    orden: int = Column(Integer, default=0)
    
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    asiento = relationship("AsientoContable", back_populates="movimientos")
    cuenta = relationship("CuentaContable", back_populates="movimientos")
    centro_costo = relationship("CentroCosto", back_populates="movimientos")

    def __repr__(self):
        return f"<MovimientoAsiento(asiento_id={self.asiento_id}, cuenta_id={self.cuenta_id})>"
