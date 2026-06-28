"""
Modelos para Contabilidad Electrónica y Obligaciones Fiscales
Incluye: DIOT, CFDI, balanzas electrónicas, retenciones
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TipoComprobante(str, enum.Enum):
    """Tipos de comprobantes fiscales (CFDI)"""
    INGRESO = "ingreso"  # Factura
    EGRESO = "egreso"  # Nota de crédito/débito
    TRASLADO = "traslado"  # Carta porte
    NOMINA = "nomina"
    PAGO = "pago"  # Recibo de pago
    RETENCION = "retencion"


class TipoOperacion(str, enum.Enum):
    """Tipo de operación para DIOT"""
    NACIONAL = "nacional"
    EXTRANJERO = "extranjero"


class PeriodoFiscal(Base):
    """Períodos fiscales para reportes obligatorios"""
    __tablename__ = "periodos_fiscales"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)  # 1-12
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), default='abierto')  # abierto, cerrado, presentado
    diot_presentada = Column(Boolean, default=False)
    balanza_presentada = Column(Boolean, default=False)
    fecha_cierre = Column(DateTime(timezone=True))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class ConfiguracionFiscal(Base):
    """Configuración fiscal del tenant"""
    __tablename__ = "configuracion_fiscal"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, unique=True, index=True)
    rfc = Column(String(13), nullable=False)  # RFC empresa
    razon_social = Column(String(200), nullable=False)
    regimen_fiscal = Column(String(50))  # Código régimen SAT
    codigo_postal = Column(String(10))
    certificado_sello_digital = Column(Text)  # CSD
    clave_certificado = Column(String(50))  # No. Certificado
    contraseña_csd = Column(String(200))  # Encriptada
    firma_electronica = Column(Text)  # FIEL
    configuracion_pac = Column(Text)  # JSON config Proveedor Autorización Certificación
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class CFDI(Base):
    """Comprobantes Fiscales Digitales por Internet"""
    __tablename__ = "cfdi"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    uuid = Column(String(36), unique=True)  # UUID del SAT
    folio_fiscal = Column(String(50))  # Folio interno
    tipo_comprobante = Column(SQLEnum(TipoComprobante), nullable=False)
    serie = Column(String(20))
    folio = Column(String(20))
    fecha_emision = Column(DateTime(timezone=True), nullable=False)
    fecha_timbrado = Column(DateTime(timezone=True))  # Fecha sellado SAT
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    descuento = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)
    moneda = Column(String(10), default='MXN')
    tipo_cambio = Column(Numeric(10, 4), default=1)
    metodo_pago = Column(String(20))  # PUE, PPD
    forma_pago = Column(String(20))  # 01-Efectivo, 03-Transferencia, etc.
    lugar_expedicion = Column(String(10))  # Código postal
    sello_digital = Column(Text)  # Sello digital del CFDI
    sello_sat = Column(Text)  # Sello digital del SAT
    cadena_original = Column(Text)  # Cadena original del complemento
    numero_certificado = Column(String(50))
    xml_original = Column(Text)  # XML timbrado
    xml_timbrado = Column(Text)  # XML con timbre
    estado_cfdi = Column(String(20), default='vigente')  # vigente, cancelado, suspendido
    fecha_cancelacion = Column(DateTime(timezone=True))
    motivo_cancelacion = Column(String(50))  # 01, 02, 03, 04, 05
    relacion_cfdi = Column(String(50))  # UUID relacionado
    tipo_relacion = Column(String(20))  # 01-Nota de crédito, etc.
    entidad_fiscal = Column(String(50))  # Entidad federativa
    registro_contable = Column(Boolean, default=False)  # ¿Ya se registró en contabilidad?
    asiento_id = Column(Integer, ForeignKey('asientos_contables.id'))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class DetalleCFDI(Base):
    """Conceptos del CFDI"""
    __tablename__ = "detalle_cfdi"
    
    id = Column(Integer, primary_key=True, index=True)
    cfdi_id = Column(Integer, ForeignKey('cfdi.id'), nullable=False)
    numero_concepto = Column(Integer, nullable=False)
    clave_prod_serv = Column(String(20))  # Clave producto/servicio SAT
    cantidad = Column(Numeric(15, 4), nullable=False, default=1)
    unidad = Column(String(50))  # Clave unidad SAT
    descripcion = Column(Text, nullable=False)
    valor_unitario = Column(Numeric(15, 2), nullable=False)
    importe = Column(Numeric(15, 2), nullable=False)
    descuento = Column(Numeric(15, 2), default=0)
    clave_objeto_imp = Column(String(10), default='02')  # Objeto de impuesto
    
    cfdi = relationship("CFDI", back_populates="conceptos")


class ImpuestoCFDI(Base):
    """Impuestos desglosados en CFDI"""
    __tablename__ = "impuestos_cfdi"
    
    id = Column(Integer, primary_key=True, index=True)
    detalle_cfdi_id = Column(Integer, ForeignKey('detalle_cfdi.id'), nullable=False)
    tipo_impuesto = Column(String(20))  # IVA, ISR, IEPS
    tipo_factor = Column(String(20))  # Tasa, Cuota, Exento
    tasa_o_cuota = Column(Numeric(10, 4))
    importe = Column(Numeric(15, 2), nullable=False, default=0)
    base = Column(Numeric(15, 2), nullable=False)
    es_traslado = Column(Boolean, default=True)  # True=Traslado, False=Retención
    
    detalle = relationship("DetalleCFDI", back_populates="impuestos")


class DIOT(Base):
    """Declaración Informativa de Operaciones con Terceros"""
    __tablename__ = "diot"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    periodo = Column(String(7))  # Formato: AAAA-MM
    rfc_proveedor = Column(String(13), nullable=False, index=True)
    nombre_proveedor = Column(String(200))
    tipo_operacion = Column(SQLEnum(TipoOperacion), nullable=False)
    operaciones_nacionales = Column(Numeric(15, 2), default=0)
    operaciones_globales = Column(Numeric(15, 2), default=0)
    iva_acreditable = Column(Numeric(15, 2), default=0)
    iva_no_acreditable = Column(Numeric(15, 2), default=0)
    isr_retenido = Column(Numeric(15, 2), default=0)
    iva_retenido = Column(Numeric(15, 2), default=0)
    ieps_retenido = Column(Numeric(15, 2), default=0)
    total_operacion = Column(Numeric(15, 2))
    presentada = Column(Boolean, default=False)
    fecha_presentacion = Column(DateTime(timezone=True))
    numero_presentacion = Column(String(50))  # Número de operación del SAT
    observaciones = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class Retencion(Base):
    """Retenciones de impuestos (ISR, IVA, IEPS)"""
    __tablename__ = "retenciones"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    tipo_retencion = Column(String(20), nullable=False)  # ISR, IVA, IEPS
    concepto = Column(String(200))  # Honorarios, arrendamiento, etc.
    base_retencion = Column(Numeric(15, 2), nullable=False)
    tasa_retencion = Column(Numeric(10, 4), nullable=False)
    monto_retencion = Column(Numeric(15, 2), nullable=False)
    documento_origen = Column(String(50))  # Folio factura/proveedor
    rfc_tercero = Column(String(13), nullable=False)
    periodo_fiscal = Column(String(7))  # AAAA-MM
    registrada_contablemente = Column(Boolean, default=False)
    asiento_id = Column(Integer, ForeignKey('asientos_contables.id'))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class ConstanciaRetencion(Base):
    """Constancias de retenciones anuales"""
    __tablename__ = "constancias_retencion"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    rfc_tercero = Column(String(13), nullable=False)
    nombre_tercero = Column(String(200), nullable=False)
    tipo_constancia = Column(String(50))  # Servicios, Arrendamiento, Dividendos
    total_retenciones_isr = Column(Numeric(15, 2), default=0)
    total_retenciones_iva = Column(Numeric(15, 2), default=0)
    total_retenciones_ieps = Column(Numeric(15, 2), default=0)
    total_pagos = Column(Numeric(15, 2), default=0)
    xml_constancia = Column(Text)  # XML generado
    pdf_constancia = Column(Text)  # PDF generado (base64)
    fecha_emision = Column(DateTime(timezone=True))
    enviada = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class BalanzaElectronica(Base):
    """Balanza electrónica mensual"""
    __tablename__ = "balanza_electronica"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    periodo = Column(String(7))  # AAAA-MM
    tipo_balanza = Column(String(20), default='normal')  # normal, complementaria, extemporánea
    xml_balanza = Column(Text)  # XML generado
    fecha_generacion = Column(DateTime(timezone=True))
    fecha_presentacion = Column(DateTime(timezone=True))
    numero_presentacion = Column(String(50))
    estado = Column(String(20), default='generada')  # generada, presentada, rechazada, aceptada
    observaciones = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class CatalogoSAT(Base):
    """Catálogos del SAT (producto/servicio, unidad, objeto impuesto)"""
    __tablename__ = "catalogos_sat"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_catalogo = Column(String(50), nullable=False, index=True)  # prod_serv, unidad, etc.
    codigo = Column(String(20), nullable=False)
    descripcion = Column(String(500), nullable=False)
    texto_ayuda = Column(String(1000))
    fecha_inicio_vigencia = Column(Date)
    fecha_fin_vigencia = Column(Date)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
