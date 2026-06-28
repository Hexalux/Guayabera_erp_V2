"""
Modelos de Bancos - Sprint 6 (implementado anticipadamente para CXC)
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint, Index, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TipoCuentaBancaria(enum.Enum):
    """Tipos de cuentas bancarias"""
    CORRIENTE = "corriente"
    AHORROS = "ahorros"
    PLAZO_FIJO = "plazo_fijo"
    MONEDA_EXTRANJERA = "moneda_extranjera"
    OTROS_FONDOS = "otros_fondos"


class EstadoCheque(enum.Enum):
    """Estados de cheques"""
    ELABORADO = "elaborado"
    ENTREGADO = "entregado"
    COBRADO = "cobrado"
    ANULADO = "anulado"
    REBOTADO = "rebotado"
    POSFECHADO = "posfechado"
    EN_TRANSITO = "en_transito"


class Banco(Base):
    """
    Catálogo de bancos
    """
    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    nombre_corto = Column(String(50))
    
    # Datos de contacto
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(100))
    pagina_web = Column(String(200))
    
    # Códigos bancarios
    codigo_banco = Column(String(10))  # Código del banco en el país
    swift = Column(String(20))
    abi = Column(String(20))
    
    activo = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant")
    cuentas = relationship("CuentaBancaria", back_populates="banco", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'codigo', name='uq_banco_tenant_codigo'),
        Index('idx_banco_nombre', 'nombre'),
    )


class CuentaBancaria(Base):
    """
    Cuentas bancarias de la empresa
    Similar a la estructura robusta de CONTPAQi
    """
    __tablename__ = "cuentas_bancarias"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    banco_id = Column(Integer, ForeignKey("bancos.id"), nullable=False)
    
    # Identificación
    codigo = Column(String(20), nullable=False)
    numero_cuenta = Column(String(50), nullable=False, index=True)
    tipo_cuenta = Column(SQLEnum(TipoCuentaBancaria), default=TipoCuentaBancaria.CORRIENTE)
    
    # Información adicional
    sucursal = Column(String(100))
    agencia = Column(String(100))
    direccion_sucursal = Column(Text)
    
    # Moneda
    moneda = Column(String(10), nullable=False, default="USD")
    
    # Saldos
    saldo_libro = Column(Numeric(15, 4), default=0.0)  # Saldo según contabilidad
    saldo_banco = Column(Numeric(15, 4), default=0.0)  # Saldo según extracto bancario
    saldo_disponible = Column(Numeric(15, 4), default=0.0)
    cheques_por_cobrar = Column(Numeric(15, 4), default=0.0)
    cheques_por_pagar = Column(Numeric(15, 4), default=0.0)
    
    # Conciliación
    ultima_conciliacion_fecha = Column(Date)
    ultima_conciliacion_hasta = Column(Date)
    
    # Contabilidad
    cuenta_contable = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Configuración
    es_predeterminada = Column(Boolean, default=False)
    permite_saldo_negativo = Column(Boolean, default=False)
    limite_saldo_negativo = Column(Numeric(15, 4), default=0.0)
    activa = Column(Boolean, default=True)
    
    # Control de cheques
    siguiente_cheque = Column(String(20))
    ultimo_cheque_usado = Column(String(20))
    
    # Auditoría
    observaciones = Column(Text)
    
    fecha_apertura = Column(Date)
    fecha_cierre = Column(Date)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant")
    banco = relationship("Banco", back_populates="cuentas")
    movimientos = relationship("MovimientoBancario", back_populates="cuenta", cascade="all, delete-orphan")
    cheques = relationship("ChequeEmitido", back_populates="cuenta", cascade="all, delete-orphan")
    conciliaciones = relationship("ConciliacionBancaria", back_populates="cuenta", cascade="all, delete-orphan")
    centro_costo = relationship("CentroCosto")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'numero_cuenta', name='uq_cuenta_tenant_numero'),
        Index('idx_cuenta_banco', 'banco_id'),
        Index('idx_cuenta_activa', 'activa'),
    )


class MovimientoBancario(Base):
    """
    Movimientos bancarios (ingresos y egresos)
    Permite conciliación bancaria estilo CONTPAQi
    """
    __tablename__ = "movimientos_bancarios"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("cuentas_bancarias.id"), nullable=False, index=True)
    
    # Identificación
    numero_movimiento = Column(String(50), nullable=False, index=True)
    tipo_movimiento = Column(String(20), nullable=False)  # ingreso, egreso, transferencia, nota_debito, nota_credito
    
    # Fecha
    fecha_registro = Column(Date, nullable=False)
    fecha_valor = Column(Date)  # Fecha de valor bancario
    fecha_conciliacion = Column(Date)
    
    # Valores
    monto = Column(Numeric(15, 4), nullable=False)
    saldo_anterior = Column(Numeric(15, 4))
    saldo_posterior = Column(Numeric(15, 4))
    
    # Concepto
    concepto = Column(String(200), nullable=False)
    descripcion = Column(Text)
    referencia = Column(String(100))  # Referencia bancaria
    numero_documento = Column(String(50))  # Cheque, transferencia, etc.
    
    # Tercero relacionado
    tercero_id = Column(Integer, ForeignKey("terceros.id"))
    
    # Conciliación
    esta_conciliado = Column(Boolean, default=False)
    conciliacion_id = Column(Integer, ForeignKey("conciliaciones_bancarias.id"))
    diferencia_conciliacion = Column(Numeric(15, 4), default=0.0)
    
    # Contabilidad
    cuenta_contable = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    generado_contabilidad = Column(Boolean, default=False)
    
    # Origen del movimiento
    origen = Column(String(50))  # cxc, cxp, caja, manual, sistema
    documento_origen_tipo = Column(String(50))
    documento_origen_id = Column(Integer)
    
    # Auditoría
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    conciliado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    cuenta = relationship("CuentaBancaria", back_populates="movimientos")
    tercero = relationship("Tercero")
    centro_costo = relationship("CentroCosto")
    asiento_contable = relationship("AsientoContable")
    conciliacion = relationship("ConciliacionBancaria", back_populates="movimientos")
    
    __table_args__ = (
        Index('idx_movimiento_fecha', 'fecha_registro'),
        Index('idx_movimiento_conciliado', 'esta_conciliado'),
        Index('idx_movimiento_tipo', 'tipo_movimiento'),
    )


class ChequeEmitido(Base):
    """
    Control de cheques emitidos (funcionalidad clave de CONTPAQi)
    """
    __tablename__ = "cheques_emitidos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("cuentas_bancarias.id"), nullable=False, index=True)
    
    # Identificación del cheque
    numero_cheque = Column(String(20), nullable=False, index=True)
    estado = Column(SQLEnum(EstadoCheque), default=EstadoCheque.ELABORADO)
    
    # Beneficiario
    beneficiario_id = Column(Integer, ForeignKey("terceros.id"))
    beneficiario_nombre = Column(String(200), nullable=False)
    beneficiario_ruc = Column(String(50))
    
    # Valores
    monto = Column(Numeric(15, 4), nullable=False)
    moneda = Column(String(10), default="USD")
    
    # Fechas
    fecha_emision = Column(Date, nullable=False)
    fecha_entrega = Column(Date)
    fecha_cobro = Column(Date)
    fecha_rebote = Column(Date)
    fecha_anulacion = Column(Date)
    
    # Motivos
    motivo_anulacion = Column(Text)
    motivo_rebote = Column(Text)
    
    # Concepto
    concepto = Column(String(200))
    descripcion = Column(Text)
    
    # Contabilidad
    cuenta_contable = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Relación con pagos
    pago_cxp_id = Column(Integer)  # Referencia a pago de CXP
    documento_relacionado = Column(String(50))
    
    # Auditoría
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    elaborado_por = Column(Integer, ForeignKey("usuarios.id"))
    entregado_por = Column(Integer, ForeignKey("usuarios.id"))
    anulado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant")
    cuenta = relationship("CuentaBancaria", back_populates="cheques")
    beneficiario = relationship("Tercero")
    centro_costo = relationship("CentroCosto")
    asiento_contable = relationship("AsientoContable")
    elaborador = relationship("Usuario", foreign_keys=[elaborado_por])
    entregador = relationship("Usuario", foreign_keys=[entregado_por])
    anulador = relationship("Usuario", foreign_keys=[anulado_por])
    
    __table_args__ = (
        UniqueConstraint('cuenta_id', 'numero_cheque', name='uq_cuenta_cheque_numero'),
        Index('idx_cheque_estado', 'estado'),
        Index('idx_cheque_fecha', 'fecha_emision'),
    )


class ChequeRebotado(Base):
    """
    Registro de cheques rebotados
    """
    __tablename__ = "cheques_rebotados"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    cheque_id = Column(Integer, ForeignKey("cheques_emitidos.id"), nullable=False, index=True)
    
    # Datos del rebote
    fecha_rebote = Column(Date, nullable=False)
    motivo_rebote = Column(String(200), nullable=False)
    codigo_motivo = Column(String(20))  # Código del motivo según banco
    
    # Valores
    monto_cheque = Column(Numeric(15, 4), nullable=False)
    comision_bancaria = Column(Numeric(15, 4), default=0.0)
    total_recobrar = Column(Numeric(15, 4))
    
    # Gestión
    gestion_realizada = Column(Text)
    fecha_solucion = Column(Date)
    solucion = Column(String(100))  # reemplazado, pagado_efectivo, castigado
    
    # Contabilidad
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant")
    cheque = relationship("ChequeEmitido")
    asiento_contable = relationship("AsientoContable")
    registrador = relationship("Usuario")


class ConciliacionBancaria(Base):
    """
    Conciliación bancaria (funcionalidad clave de CONTPAQi y Management Pro)
    """
    __tablename__ = "conciliaciones_bancarias"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("cuentas_bancarias.id"), nullable=False, index=True)
    
    # Identificación
    numero_conciliacion = Column(String(50), nullable=False)
    
    # Periodo
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    fecha_elaboracion = Column(DateTime, default=datetime.utcnow)
    
    # Saldos
    saldo_libro_inicial = Column(Numeric(15, 4), nullable=False)
    saldo_banco_inicial = Column(Numeric(15, 4), nullable=False)
    
    # Depósitos en tránsito
    total_depositos_transito = Column(Numeric(15, 4), default=0.0)
    
    # Cheques en tránsito
    total_cheques_transito = Column(Numeric(15, 4), default=0.0)
    
    # Notas de débito/crédito no registradas
    notas_debito = Column(Numeric(15, 4), default=0.0)
    notas_credito = Column(Numeric(15, 4), default=0.0)
    
    # Errores
    errores_libro = Column(Numeric(15, 4), default=0.0)
    errores_banco = Column(Numeric(15, 4), default=0.0)
    
    # Saldos finales
    saldo_libro_ajustado = Column(Numeric(15, 4))
    saldo_banco_ajustado = Column(Numeric(15, 4))
    diferencia = Column(Numeric(15, 4), default=0.0)
    
    # Estado
    estado = Column(String(20), default="borrador")  # borrador, cuadrada, conciliada, anulada
    esta_cuadrada = Column(Boolean, default=False)
    
    # Auditoría
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    elaborada_por = Column(Integer, ForeignKey("usuarios.id"))
    revisada_por = Column(Integer, ForeignKey("usuarios.id"))
    aprobada_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant")
    cuenta = relationship("CuentaBancaria", back_populates="conciliaciones")
    movimientos = relationship("MovimientoBancario", back_populates="conciliacion")
    elaborador = relationship("Usuario", foreign_keys=[elaborada_por])
    revisor = relationship("Usuario", foreign_keys=[revisada_por])
    aprobador = relationship("Usuario", foreign_keys=[aprobada_por])
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'numero_conciliacion', name='uq_conciliacion_numero'),
        Index('idx_conciliacion_fechas', 'fecha_desde', 'fecha_hasta'),
        Index('idx_conciliacion_estado', 'estado'),
    )


class SolicitudCheque(Base):
    """
    Solicitud de cheques (flujo de autorización estilo Management Pro)
    """
    __tablename__ = "solicitudes_cheques"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    numero_solicitud = Column(String(50), nullable=False, unique=True)
    
    # Solicitante
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    departamento = Column(String(100))
    
    # Datos del cheque
    cuenta_bancaria_id = Column(Integer, ForeignKey("cuentas_bancarias.id"), nullable=False)
    beneficiario_nombre = Column(String(200), nullable=False)
    beneficiario_ruc = Column(String(50))
    monto = Column(Numeric(15, 4), nullable=False)
    concepto = Column(String(200), nullable=False)
    
    # Autorizaciones
    estado = Column(String(20), default="pendiente")  # pendiente, aprobada, rechazada, elaborada
    autorizado_por_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_autorizacion = Column(DateTime)
    observaciones_autorizacion = Column(Text)
    
    # Cheque resultante
    cheque_id = Column(Integer, ForeignKey("cheques_emitidos.id"))
    
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant")
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    cuenta_bancaria = relationship("CuentaBancaria")
    autorizador = relationship("Usuario", foreign_keys=[autorizado_por_id])
    cheque = relationship("ChequeEmitido")
    
    __table_args__ = (
        Index('idx_solicitud_estado', 'estado'),
        Index('idx_solicitud_fecha', 'fecha_solicitud'),
    )


# Importar modelos relacionados
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.contabilidad import CentroCosto, AsientoContable
from app.models.terceros import Tercero
