"""
Guayabera ERP Suite v2.0 - Sprint 4: Cuentas por Pagar (CXP)
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TipoDocumentoCXP(str, enum.Enum):
    FACTURA = "factura"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    RECIBO = "recibo"
    PAGARE = "pagare"
    RETENCION = "retencion"
    OTRO = "otro"


class EstadoPago(str, enum.Enum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADO = "pagado"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"


class MetodoPago(str, enum.Enum):
    EFECTIVO = "efectivo"
    CHEQUE = "cheque"
    TRANSFERENCIA = "transferencia"
    TARJETA = "tarjeta"
    MONEDERO_ELECTRONICO = "monedero_electronico"
    DACION_EN_PAGO = "dacion_en_pago"


class CondicionPago(str, enum.Enum):
    CONTADO = "contado"
    CREDITO_7_DIAS = "credito_7_dias"
    CREDITO_15_DIAS = "credito_15_dias"
    CREDITO_30_DIAS = "credito_30_dias"
    CREDITO_60_DIAS = "credito_60_dias"
    CREDITO_90_DIAS = "credito_90_dias"
    PERSONALIZADO = "personalizado"


class Proveedor(Base):
    """
    Modelo de Proveedores (hereda características de TerceroBase)
    Inspirado en CONTPAQi: datos fiscales completos, límites de crédito
    Inspirado en Odoo: categorías, etiquetas, flexibilidad
    """
    __tablename__ = "proveedores"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Datos básicos
    rfc = Column(String(13), unique=True, nullable=False, index=True)
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200))
    regimen_fiscal = Column(String(100))
    codigo_postal = Column(String(10))
    
    # Datos de contacto
    email = Column(String(100))
    telefono = Column(String(20))
    celular = Column(String(20))
    direccion = Column(Text)
    colonia = Column(String(100))
    ciudad = Column(String(100))
    estado = Column(String(100))
    pais = Column(String(50), default="México")
    
    # Configuración financiera
    limite_credito = Column(Float, default=0.0)
    dias_credito = Column(Integer, default=30)
    descuento_porcentaje = Column(Float, default=0.0)
    moneda_principal = Column(String(3), default="MXN")
    
    # Datos bancarios
    banco = Column(String(100))
    clabe = Column(String(18))
    cuenta_bancaria = Column(String(20))
    
    # Control
    activo = Column(Boolean, default=True)
    requiere_autorizacion_pagos = Column(Boolean, default=False)
    nivel_autorizacion = Column(Integer, default=1)  # 1-5 según monto
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    facturas = relationship("FacturaProveedor", back_populates="proveedor", cascade="all, delete-orphan")
    pagos = relationship("PagoProveedor", back_populates="proveedor", cascade="all, delete-orphan")
    notas_credito = relationship("NotaCreditoProveedor", back_populates="proveedor", cascade="all, delete-orphan")
    anticipos = relationship("AnticipoProveedor", back_populates="proveedor", cascade="all, delete-orphan")


class FacturaProveedor(Base):
    """
    Facturas de proveedores con validación de pagos pendientes
    Similar a CONTPAQi: folio fiscal, UUID, timbrado
    """
    __tablename__ = "facturas_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    
    # Datos del documento
    tipo_documento = Column(SQLEnum(TipoDocumentoCXP), default=TipoDocumentoCXP.FACTURA)
    serie = Column(String(20))
    folio = Column(String(20), nullable=False)
    uuid_fiscal = Column(String(36), unique=True)  # UUID del CFDI
    fecha_emision = Column(Date, nullable=False)
    fecha_recepcion = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    
    # Montos
    subtotal = Column(Float, nullable=False, default=0.0)
    descuento = Column(Float, default=0.0)
    impuestos_trasladados = Column(Float, default=0.0)
    impuestos_retenidos = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    saldo_pendiente = Column(Float, nullable=False, default=0.0)
    anticipo_aplicado = Column(Float, default=0.0)
    
    # Moneda y tipo de cambio
    moneda = Column(String(3), default="MXN")
    tipo_cambio = Column(Float, default=1.0)
    total_mn = Column(Float, default=0.0)  # Total en moneda nacional
    
    # Estado y control
    estado_pago = Column(SQLEnum(EstadoPago), default=EstadoPago.PENDIENTE)
    condicion_pago = Column(SQLEnum(CondicionPago), default=CondicionPago.CREDITO_30_DIAS)
    metodo_pago = Column(SQLEnum(MetodoPago))
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Observaciones
    observaciones = Column(Text)
    referencia = Column(String(100))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    autorizado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_autorizacion = Column(DateTime)
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="facturas")
    movimientos = relationship("MovimientoFacturaProveedor", back_populates="factura", cascade="all, delete-orphan")
    retenciones = relationship("RetencionProveedor", back_populates="factura", cascade="all, delete-orphan")


class PagoProveedor(Base):
    """
    Pagos a proveedores con soporte para anticipos y descuentos
    Flujo de aprobación estilo Management Pro
    """
    __tablename__ = "pagos_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    
    # Datos del pago
    numero_pago = Column(String(50), unique=True, nullable=False)
    fecha_pago = Column(Date, nullable=False)
    fecha_aplicacion = Column(Date, nullable=False)
    
    # Montos
    subtotal = Column(Float, default=0.0)
    iva_retenido = Column(Float, default=0.0)
    isr_retenido = Column(Float, default=0.0)
    otros_descuentos = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    
    # Método de pago
    metodo_pago = Column(SQLEnum(MetodoPago), nullable=False)
    numero_cheque = Column(String(20))
    cuenta_bancaria_id = Column(Integer, ForeignKey("cuentas_bancarias.id"))
    clabe_destino = Column(String(18))
    
    # Referencias
    referencia_bancaria = Column(String(50))
    observaciones = Column(Text)
    
    # Estado y autorización
    estado = Column(SQLEnum(EstadoPago), default=EstadoPago.PENDIENTE)
    requiere_autorizacion = Column(Boolean, default=False)
    autorizado = Column(Boolean, default=False)
    autorizado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_autorizacion = Column(DateTime)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="pagos")
    facturas_aplicadas = relationship("AplicacionPagoFactura", back_populates="pago", cascade="all, delete-orphan")


class AplicacionPagoFactura(Base):
    """Tabla intermedia para aplicar pagos a múltiples facturas"""
    __tablename__ = "aplicaciones_pago_factura"
    
    id = Column(Integer, primary_key=True, index=True)
    pago_id = Column(Integer, ForeignKey("pagos_proveedor.id"), nullable=False)
    factura_id = Column(Integer, ForeignKey("facturas_proveedor.id"), nullable=False)
    monto_aplicado = Column(Float, nullable=False, default=0.0)
    fecha_aplicacion = Column(DateTime, default=datetime.utcnow)
    
    pago = relationship("PagoProveedor", back_populates="facturas_aplicadas")
    factura = relationship("FacturaProveedor")


class NotaCreditoProveedor(Base):
    """
    Notas de crédito de proveedores (devoluciones, bonificaciones)
    Múltiples tipos como en CONTPAQi
    """
    __tablename__ = "notas_credito_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    
    # Datos del documento
    serie = Column(String(20))
    folio = Column(String(20), nullable=False)
    uuid_fiscal = Column(String(36), unique=True)
    fecha_emision = Column(Date, nullable=False)
    tipo_nota = Column(String(50))  # Devolución, Bonificación, Descuento
    
    # Montos
    subtotal = Column(Float, default=0.0)
    impuestos = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    saldo_disponible = Column(Float, nullable=False, default=0.0)
    
    # Relación con factura original
    factura_origen_id = Column(Integer, ForeignKey("facturas_proveedor.id"))
    
    # Estado
    aplicada = Column(Boolean, default=False)
    fecha_aplicacion = Column(DateTime)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="notas_credito")


class AnticipoProveedor(Base):
    """Anticipos a proveedores aplicables a futuras facturas"""
    __tablename__ = "anticipos_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    
    # Datos
    numero_anticipo = Column(String(50), unique=True, nullable=False)
    fecha_anticipo = Column(Date, nullable=False)
    descripcion = Column(Text)
    
    # Montos
    monto = Column(Float, nullable=False, default=0.0)
    iva_trasladado = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    saldo_disponible = Column(Float, nullable=False, default=0.0)
    
    # Documento de respaldo
    numero_documento = Column(String(50))
    uuid_fiscal = Column(String(36))
    
    # Estado
    aplicado = Column(Boolean, default=False)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="anticipos")


class RetencionProveedor(Base):
    """Retenciones de impuestos (ISR, IVA, IEPS)"""
    __tablename__ = "retenciones_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    factura_id = Column(Integer, ForeignKey("facturas_proveedor.id"), nullable=False)
    
    # Tipo de retención
    tipo_impuesto = Column(String(10), nullable=False)  # ISR, IVA, IEPS
    tasa_retencion = Column(Float, nullable=False)
    base_retencion = Column(Float, nullable=False)
    monto_retencion = Column(Float, nullable=False)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    factura = relationship("FacturaProveedor", back_populates="retenciones")


class MovimientoFacturaProveedor(Base):
    """Historial de movimientos de cada factura (pagos parciales, notas)"""
    __tablename__ = "movimientos_factura_proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    factura_id = Column(Integer, ForeignKey("facturas_proveedor.id"), nullable=False)
    
    # Tipo de movimiento
    tipo_movimiento = Column(String(50), nullable=False)  # Pago parcial, Nota crédito, etc.
    documento_referencia = Column(String(50))
    
    # Montos
    cargo = Column(Float, default=0.0)
    abono = Column(Float, default=0.0)
    saldo_anterior = Column(Float, default=0.0)
    saldo_nuevo = Column(Float, default=0.0)
    
    # Fecha y descripción
    fecha_movimiento = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(Text)
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    factura = relationship("FacturaProveedor", back_populates="movimientos")


class ParametrosCXP(Base):
    """Parámetros de configuración del módulo CXP"""
    __tablename__ = "parametros_cxp"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    
    # Configuración general
    prefijo_pago = Column(String(10), default="PAG")
    consecutivo_pago = Column(Integer, default=1)
    
    # Autorizaciones
    nivel1_monto_maximo = Column(Float, default=10000.0)
    nivel2_monto_maximo = Column(Float, default=50000.0)
    nivel3_monto_maximo = Column(Float, default=100000.0)
    
    # Contabilidad automática
    generar_poliza_automatica = Column(Boolean, default=True)
    cuenta_proveedores = Column(String(20))
    cuenta_bancos = Column(String(20))
    cuenta_iva_acreditable = Column(String(20))
    cuenta_isr_retener = Column(String(20))
    
    # Auditoría
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
