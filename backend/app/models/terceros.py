"""
Modelos de Terceros Unificados - Sprint 2
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TipoTercero(enum.Enum):
    """Tipos de terceros soportados"""
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    CLIENTE_PROVEEDOR = "cliente_proveedor"
    EMPLEADO = "empleado"
    OTRO = "otro"


class TipoDocumento(enum.Enum):
    """Tipos de documentos de identidad"""
    CEDULA = "cedula"
    RUC = "ruc"
    PASAPORTE = "pasaporte"
    NIT = "nit"
    OTRO = "otro"


class EstadoTercero(enum.Enum):
    """Estado del tercero"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    BLOQUEADO = "bloqueado"
    SUSPENDIDO = "suspendido"


class Tercero(Base):
    """
    Modelo unificado de terceros (Clientes, Proveedores, etc.)
    Inspirado en la estructura robusta de CONTPAQi con flexibilidad de Odoo
    """
    __tablename__ = "terceros"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Datos básicos
    codigo = Column(String(20), nullable=False, index=True)  # Código interno
    tipo_tercero = Column(SQLEnum(TipoTercero), nullable=False, default=TipoTercero.CLIENTE)
    nombre_comercial = Column(String(200), nullable=False)
    razon_social = Column(String(200))
    
    # Datos fiscales
    tipo_documento = Column(SQLEnum(TipoDocumento), default=TipoDocumento.RUC)
    numero_documento = Column(String(50), nullable=False, index=True)
    digito_verificador = Column(String(10))
    contribuyente_especial = Column(Boolean, default=False)
    agente_retencion = Column(Boolean, default=False)
    
    # Clasificación
    estado = Column(SQLEnum(EstadoTercero), default=EstadoTercero.ACTIVO)
    categoria = Column(String(50))  # A, B, C según importancia
    segmento = Column(String(50))   # Corporativo, PYME, Persona natural
    
    # Datos de contacto principal
    email = Column(String(100), index=True)
    email_alternativo = Column(String(100))
    telefono_principal = Column(String(20))
    telefono_secundario = Column(String(20))
    celular = Column(String(20))
    fax = Column(String(20))
    
    # Dirección fiscal
    direccion_principal = Column(Text)
    ciudad = Column(String(100))
    provincia = Column(String(100))
    codigo_postal = Column(String(20))
    pais = Column(String(50), default="Ecuador")
    
    # Datos crediticios (CONTPAQi style)
    limite_credito = Column(Float, default=0.0)
    credito_disponible = Column(Float, default=0.0)
    plazo_pago_dias = Column(Integer, default=30)
    descuento_porcentaje = Column(Float, default=0.0)
    nivel_riesgo = Column(String(20), default="normal")  # bajo, normal, alto, critico
    
    # Configuración contable
    cuenta_contable_cxc = Column(String(20))  # Para clientes
    cuenta_contable_cxp = Column(String(20))  # Para proveedores
    cuenta_contable_anticipos = Column(String(20))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Configuración de ventas/compras
    vendedor_id = Column(Integer)  # Referencia a usuario/vendedor
    zona_venta = Column(String(50))
    ruta_entrega = Column(String(50))
    lista_precios_id = Column(Integer)
    moneda_id = Column(Integer, ForeignKey("monedas.id", ondelete="SET NULL"))
    
    # Flags de comportamiento
    requiere_orden_compra = Column(Boolean, default=False)
    permite_saldo_negativo = Column(Boolean, default=False)
    bloquear_ventas_vencidas = Column(Boolean, default=False)
    enviar_estado_cuenta_email = Column(Boolean, default=True)
    
    # Datos adicionales
    pagina_web = Column(String(200))
    contacto_principal = Column(String(100))
    cargo_contacto = Column(String(100))
    observaciones = Column(Text)
    referencia_comercial_1 = Column(Text)
    referencia_comercial_2 = Column(Text)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_ultimo_movimiento = Column(DateTime)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="terceros")
    direcciones = relationship("TerceroDireccion", back_populates="tercero", cascade="all, delete-orphan")
    contactos = relationship("TerceroContacto", back_populates="tercero", cascade="all, delete-orphan")
    cuentas_bancarias = relationship("TerceroCuentaBancaria", back_populates="tercero", cascade="all, delete-orphan")
    documentos = relationship("TerceroDocumento", back_populates="tercero", cascade="all, delete-orphan")
    movimientos_cxc = relationship("CXCDocumento", back_populates="tercero", cascade="all, delete-orphan")
    movimientos_cxp = relationship("CXPDocumento", back_populates="tercero", cascade="all, delete-orphan")
    centro_costo = relationship("CentroCosto")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'codigo', name='uq_tercero_tenant_codigo'),
        UniqueConstraint('tenant_id', 'numero_documento', name='uq_tercero_tenant_documento'),
        Index('idx_tercero_nombre', 'nombre_comercial'),
        Index('idx_tercero_estado', 'estado'),
        Index('idx_tercero_tipo', 'tipo_tercero'),
    )


class TerceroDireccion(Base):
    """Direcciones múltiples para un tercero (estilo Odoo)"""
    __tablename__ = "terceros_direcciones"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    
    tipo_direccion = Column(String(20), default="adicional")  # fiscal, envio, cobranza, adicional
    descripcion = Column(String(100))
    direccion = Column(Text, nullable=False)
    ciudad = Column(String(100))
    provincia = Column(String(100))
    codigo_postal = Column(String(20))
    pais = Column(String(50), default="Ecuador")
    telefono = Column(String(20))
    email = Column(String(100))
    es_predeterminada = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    tercero = relationship("Tercero", back_populates="direcciones")
    
    __table_args__ = (
        Index('idx_direccion_tercero', 'tercero_id', 'tipo_direccion'),
    )


class TerceroContacto(Base):
    """Contactos múltiples para un tercero (estilo Odoo)"""
    __tablename__ = "terceros_contactos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    
    nombre = Column(String(100), nullable=False)
    cargo = Column(String(100))
    departamento = Column(String(100))
    email = Column(String(100))
    telefono = Column(String(20))
    celular = Column(String(20))
    extension = Column(String(10))
    es_primario = Column(Boolean, default=False)
    recibe_facturas = Column(Boolean, default=False)
    recibe_estados_cuenta = Column(Boolean, default=False)
    observaciones = Column(Text)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    tercero = relationship("Tercero", back_populates="contactos")


class TerceroCuentaBancaria(Base):
    """Cuentas bancarias del tercero para pagos/depositos"""
    __tablename__ = "terceros_cuentas_bancarias"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    
    banco_nombre = Column(String(100), nullable=False)
    tipo_cuenta = Column(String(20))  # ahorros, corriente
    numero_cuenta = Column(String(50), nullable=False)
    tipo_cuenta_bancaria = Column(String(20))  # nacional, internacional
    swift = Column(String(20))
    abi = Column(String(20))
    direccion_banco = Column(Text)
    pais = Column(String(50))
    moneda = Column(String(10), default="USD")
    es_predeterminada = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    tercero = relationship("Tercero", back_populates="cuentas_bancarias")


class TerceroDocumento(Base):
    """Documentos adjuntos del tercero (RUC, cédulas, contratos, etc.)"""
    __tablename__ = "terceros_documentos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False, index=True)
    
    tipo_documento = Column(String(50))  # RUC, cedula, contrato, referencia
    descripcion = Column(String(200))
    archivo_path = Column(String(500))
    archivo_nombre = Column(String(200))
    archivo_tipo = Column(String(50))  # pdf, jpg, png
    fecha_emision = Column(Date)
    fecha_vencimiento = Column(Date)
    numero_documento = Column(String(50))
    activo = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    tercero = relationship("Tercero", back_populates="documentos")


# Importar modelos relacionados para evitar circular imports
from app.models.contabilidad import CentroCosto
from app.models.tenant import Tenant
from app.models.usuario import Usuario
