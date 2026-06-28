"""
Modelos de Cuentas por Cobrar - Sprint 3
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint, Index, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TipoDocumentoCXC(enum.Enum):
    """Tipos de documentos en CXC"""
    FACTURA = "factura"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    RECIBO = "recibo"
    PAGARE = "pagare"
    ANTICIPO = "anticipo"
    COBRO = "cobro"
    INTERES_MORATORIO = "interes_moratorio"
    OTRO = "otro"


class EstadoDocumentoCXC(enum.Enum):
    """Estado del documento"""
    BORRADOR = "borrador"
    REGISTRADO = "registrado"
    PARCIAL = "parcial"
    SALDADO = "saldado"
    VENCIDO = "vencido"
    CANCELADO = "cancelado"
    COBRANZA = "cobranza"
    CASTIGADO = "castigado"


class EstadoCobro(enum.Enum):
    """Estado de los cobros"""
    PENDIENTE = "pendiente"
    PROCESADO = "procesado"
    APLICADO = "aplicado"
    CANCELADO = "cancelado"
    REBOTADO = "rebotado"


class CXCDocumento(Base):
    """
    Documentos de Cuentas por Cobrar
    Inspirado en la robustez de CONTPAQi con opciones de Management Pro
    """
    __tablename__ = "cxc_documentos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Identificación del documento
    codigo = Column(String(50), nullable=False, index=True)  # Código interno único
    tipo_documento = Column(SQLEnum(TipoDocumentoCXC), nullable=False)
    serie = Column(String(20))  # Serie para facturación electrónica
    secuencial = Column(String(20))  # Secuencial para facturación
    numero_autorizacion = Column(String(100))  # Autorización SRI
    
    # Tercero
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    nombre_tercero = Column(String(200))  # Snapshot del nombre al momento de crear
    
    # Datos del documento
    estado = Column(SQLEnum(EstadoDocumentoCXC), default=EstadoDocumentoCXC.BORRADOR)
    fecha_emision = Column(Date, nullable=False, index=True)
    fecha_vencimiento = Column(Date, index=True)
    fecha_limite_pago = Column(Date)
    periodo_contable = Column(String(7))  # AAAA-MM
    
    # Valores
    subtotal = Column(Numeric(15, 4), default=0.0)
    descuento = Column(Numeric(15, 4), default=0.0)
    base_imponible = Column(Numeric(15, 4), default=0.0)
    iva_porcentaje = Column(Numeric(5, 2), default=12.0)
    iva_valor = Column(Numeric(15, 4), default=0.0)
    otros_impuestos = Column(Numeric(15, 4), default=0.0)
    total = Column(Numeric(15, 4), nullable=False)
    
    # Saldos
    saldo_anterior = Column(Numeric(15, 4), default=0.0)
    abonos = Column(Numeric(15, 4), default=0.0)
    notas_credito_aplicadas = Column(Numeric(15, 4), default=0.0)
    anticipos_aplicados = Column(Numeric(15, 4), default=0.0)
    saldo_actual = Column(Numeric(15, 4), nullable=False)
    
    # Moneda
    moneda_id = Column(Integer, ForeignKey("monedas.id"))
    moneda = Column(String(10), default="USD")
    tipo_cambio = Column(Numeric(15, 6), default=1.0)
    total_moneda_local = Column(Numeric(15, 4))
    
    # Documento relacionado (para notas de crédito, devoluciones, etc.)
    documento_relacionado_id = Column(Integer, ForeignKey("cxc_documentos.id"))
    tipo_relacion = Column(String(50))  # nota_credito_a, devolucion, bonificacion
    
    # Datos de pago
    forma_pago = Column(String(50))  # efectivo, transferencia, cheque, tarjeta
    plazo_pago_dias = Column(Integer)
    permite_parcial = Column(Boolean, default=True)
    
    # Asiento contable
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    generado_contabilidad = Column(Boolean, default=False)
    fecha_contabilizacion = Column(DateTime)
    
    # Cobranza
    asignado_cobrador_id = Column(Integer, ForeignKey("usuarios.id"))
    ruta_cobranza = Column(String(50))
    gestion_cobranza = Column(Text)  # Historial de gestiones
    ultima_gestion_fecha = Column(DateTime)
    promesa_pago_fecha = Column(Date)
    promesa_pago_monto = Column(Numeric(15, 4))
    
    # Comisiones
    aplica_comision = Column(Boolean, default=False)
    porcentaje_comision = Column(Numeric(5, 2))
    valor_comision = Column(Numeric(15, 4))
    pagado_comision = Column(Boolean, default=False)
    
    # Auditoría y seguimiento
    observaciones = Column(Text)
    referencia_comercial = Column(String(100))
    orden_compra = Column(String(50))
    guia_remision = Column(String(50))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_saldo_cero = Column(DateTime)  # Cuando se saldó
    
    # Relaciones
    tenant = relationship("Tenant")
    tercero = relationship("Tercero", back_populates="movimientos_cxc")
    movimientos = relationship("CXCMovimiento", back_populates="documento", cascade="all, delete-orphan")
    notas_credito = relationship("CXCDocumento", remote_side=[documento_relacionado_id])
    asiento_contable = relationship("AsientoContable")
    cobrador = relationship("Usuario")
    documento_relacionado = relationship("CXCDocumento", remote_side=[documento_relacionado_id], foreign_keys=[documento_relacionado_id])
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'serie', 'secuencial', name='uq_cxc_serie_secuencial'),
        Index('idx_cxc_estado', 'estado'),
        Index('idx_cxc_vencimiento', 'fecha_vencimiento'),
        Index('idx_cxc_saldo', 'saldo_actual'),
        Index('idx_cxc_tercero_estado', 'tercero_id', 'estado'),
    )


class CXCMovimiento(Base):
    """
    Movimientos/abonos aplicados a documentos CXC
    Permite tracking detallado de cada aplicación de pago
    """
    __tablename__ = "cxc_movimientos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    documento_id = Column(Integer, ForeignKey("cxc_documentos.id"), nullable=False, index=True)
    
    tipo_movimiento = Column(String(50), nullable=False)  # abono, nota_credito, anticipo, interes, castigo
    numero_movimiento = Column(String(50), nullable=False, index=True)
    
    # Valores
    valor_original = Column(Numeric(15, 4), nullable=False)
    valor_aplicado = Column(Numeric(15, 4), default=0.0)
    saldo_movimiento = Column(Numeric(15, 4))
    
    # Referencias
    documento_origen_id = Column(Integer)  # ID del documento que genera el movimiento (ej: recibo de caja)
    tipo_documento_origen = Column(String(50))
    
    # Fecha
    fecha_movimiento = Column(Date, nullable=False)
    fecha_aplicacion = Column(DateTime)
    
    # Contabilidad
    cuenta_contable = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Estado
    estado = Column(String(20), default="aplicado")
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    documento = relationship("CXCDocumento", back_populates="movimientos")
    centro_costo = relationship("CentroCosto")
    asiento_contable = relationship("AsientoContable")
    
    __table_args__ = (
        Index('idx_movimiento_documento', 'documento_id', 'tipo_movimiento'),
    )


class CXCCobro(Base):
    """
    Registro de cobros realizados (similar a CONTPAQi)
    Puede aplicar a múltiples documentos
    """
    __tablename__ = "cxc_cobros"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Identificación
    codigo = Column(String(50), nullable=False, unique=True, index=True)
    numero_recibo = Column(String(50))  # Número de recibo de caja
    
    # Tercero
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    nombre_tercero = Column(String(200))
    
    # Datos del cobro
    estado = Column(SQLEnum(EstadoCobro), default=EstadoCobro.PENDIENTE)
    fecha_cobro = Column(Date, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    
    # Valores
    subtotal = Column(Numeric(15, 4), default=0.0)
    impuestos = Column(Numeric(15, 4), default=0.0)
    total = Column(Numeric(15, 4), nullable=False)
    valor_aplicado = Column(Numeric(15, 4), default=0.0)
    saldo_cobro = Column(Numeric(15, 4))
    
    # Forma de pago
    forma_pago = Column(String(50), nullable=False)  # efectivo, transferencia, cheque, tarjeta, mixto
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    numero_cheque = Column(String(50))
    numero_transaccion = Column(String(100))
    autorizacion_tarjeta = Column(String(50))
    
    # Documento de respaldo
    numero_comprobante = Column(String(50))
    serie_comprobante = Column(String(20))
    
    # Aplicaciones
    aplica_a_facturas = Column(Boolean, default=False)
    aplica_a_notas = Column(Boolean, default=False)
    deja_saldo_favor = Column(Boolean, default=False)
    
    # Contabilidad
    cuenta_contable_id = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    generado_contabilidad = Column(Boolean, default=False)
    
    # Relación de cobranza
    relacion_cobranza_id = Column(Integer, ForeignKey("cxc_relaciones_cobranza.id"))
    
    # Auditoría
    observaciones = Column(Text)
    referencia = Column(String(100))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
    anulado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_anulacion = Column(DateTime)
    motivo_anulacion = Column(Text)
    
    # Relaciones
    tenant = relationship("Tenant")
    tercero = relationship("Tercero")
    detalles = relationship("CXCCobroDetalle", back_populates="cobro", cascade="all, delete-orphan")
    centro_costo = relationship("CentroCosto")
    asiento_contable = relationship("AsientoContable")
    banco = relationship("Banco")
    relacion_cobranza = relationship("CXCRelacionCobranza")
    
    __table_args__ = (
        Index('idx_cobro_fecha', 'fecha_cobro'),
        Index('idx_cobro_estado', 'estado'),
    )


class CXCCobroDetalle(Base):
    """
    Detalle de aplicación de cobro a documentos específicos
    Permite aplicar un cobro a múltiples facturas/documentos
    """
    __tablename__ = "cxc_cobros_detalles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    cobro_id = Column(Integer, ForeignKey("cxc_cobros.id"), nullable=False, index=True)
    documento_id = Column(Integer, ForeignKey("cxc_documentos.id"), nullable=False, index=True)
    
    # Valores
    valor_documento = Column(Numeric(15, 4), nullable=False)
    saldo_documento = Column(Numeric(15, 4), nullable=False)
    valor_aplicar = Column(Numeric(15, 4), nullable=False)
    valor_aplicado = Column(Numeric(15, 4), default=0.0)
    
    # Tipo de aplicación
    tipo_aplicacion = Column(String(50))  # pago_total, pago_parcial, anticipo, nota_credito
    
    # Fechas
    fecha_documento = Column(Date)
    fecha_vencimiento = Column(Date)
    dias_mora = Column(Integer)
    
    # Auditoría
    observaciones = Column(Text)
    fecha_aplicacion = Column(DateTime, default=datetime.utcnow)
    aplicado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    cobro = relationship("CXCCobro", back_populates="detalles")
    documento = relationship("CXCDocumento")
    usuario = relationship("Usuario")
    
    __table_args__ = (
        UniqueConstraint('cobro_id', 'documento_id', name='uq_cobro_detalle_documento'),
        Index('idx_detalle_documento', 'documento_id'),
    )


class CXCRelacionCobranza(Base):
    """
    Relación de cobranza (agrupación de cobros para depósito bancario)
    Similar a la funcionalidad de CONTPAQi
    """
    __tablename__ = "cxc_relaciones_cobranza"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    codigo = Column(String(50), nullable=False, unique=True)
    numero_relacion = Column(String(50))
    
    estado = Column(String(20), default="elaborada")  # elaborada, depositada, anulada
    fecha_elaboracion = Column(Date, nullable=False)
    fecha_deposito = Column(Date)
    
    # Valores
    total_efectivo = Column(Numeric(15, 4), default=0.0)
    total_cheques = Column(Numeric(15, 4), default=0.0)
    total_tarjetas = Column(Numeric(15, 4), default=0.0)
    total_transferencias = Column(Numeric(15, 4), default=0.0)
    total_general = Column(Numeric(15, 4), nullable=False)
    
    # Depósito
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    numero_deposito = Column(String(50))
    numero_boleta = Column(String(50))
    cuenta_bancaria = Column(String(50))
    
    # Auditoría
    observaciones = Column(Text)
    elaborado_por = Column(Integer, ForeignKey("usuarios.id"))
    depositado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant")
    cobros = relationship("CXCCobro", back_populates="relacion_cobranza")
    banco = relationship("Banco")
    elaborador = relationship("Usuario", foreign_keys=[elaborado_por])
    depositador = relationship("Usuario", foreign_keys=[depositado_por])


class CXCAnticipo(Base):
    """
    Anticipos de clientes (dinero recibido antes de emitir factura)
    """
    __tablename__ = "cxc_anticipos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    codigo = Column(String(50), nullable=False, index=True)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    
    estado = Column(String(20), default="disponible")  # disponible, aplicado_parcial, aplicado_total, cancelado
    
    fecha_registro = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date)
    
    # Valores
    subtotal = Column(Numeric(15, 4), default=0.0)
    impuestos = Column(Numeric(15, 4), default=0.0)
    total = Column(Numeric(15, 4), nullable=False)
    saldo = Column(Numeric(15, 4), nullable=False)
    aplicado = Column(Numeric(15, 4), default=0.0)
    
    # Origen
    forma_pago = Column(String(50))
    comprobante_pago = Column(String(50))
    referencia = Column(String(100))
    
    # Contabilidad
    cuenta_contable = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant")
    tercero = relationship("Tercero")
    aplicaciones = relationship("CXCAnticipoAplicacion", back_populates="anticipo", cascade="all, delete-orphan")
    centro_costo = relationship("CentroCosto")
    asiento_contable = relationship("AsientoContable")


class CXCAnticipoAplicacion(Base):
    """Aplicación de anticipo a documentos específicos"""
    __tablename__ = "cxc_anticipos_aplicaciones"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    anticipo_id = Column(Integer, ForeignKey("cxc_anticipos.id"), nullable=False, index=True)
    documento_id = Column(Integer, ForeignKey("cxc_documentos.id"), nullable=False, index=True)
    
    valor_aplicado = Column(Numeric(15, 4), nullable=False)
    fecha_aplicacion = Column(DateTime, default=datetime.utcnow)
    observaciones = Column(Text)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    anticipo = relationship("CXCAnticipo", back_populates="aplicaciones")
    documento = relationship("CXCDocumento")
    usuario = relationship("Usuario")
    
    __table_args__ = (
        UniqueConstraint('anticipo_id', 'documento_id', name='uq_anticipo_documento'),
    )


class CXCInteresMoratorio(Base):
    """
    Generación de intereses moratorios por pagos vencidos
    """
    __tablename__ = "cxc_intereses_moratorios"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    codigo = Column(String(50), nullable=False, unique=True)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False)
    
    estado = Column(String(20), default="calculado")  # calculado, generado, cancelado
    
    # Periodo de cálculo
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    
    # Tasas
    tasa_anual = Column(Numeric(5, 2), nullable=False)
    tasa_diaria = Column(Numeric(5, 4))
    
    # Cálculos
    capital_base = Column(Numeric(15, 4), nullable=False)
    dias_mora = Column(Integer, nullable=False)
    interes_calculado = Column(Numeric(15, 4), nullable=False)
    
    # Documento generado
    documento_id = Column(Integer, ForeignKey("cxc_documentos.id"))
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    observaciones = Column(Text)
    calculado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant")
    tercero = relationship("Tercero")
    documento = relationship("CXCDocumento")
    asiento_contable = relationship("AsientoContable")
    calculador = relationship("Usuario")


# Importar modelos relacionados
from app.models.tenant import Tenant
from app.models.terceros import Tercero
from app.models.contabilidad import CentroCosto, AsientoContable
from app.models.usuario import Usuario
from app.models.tesoreria.bancos import Banco
