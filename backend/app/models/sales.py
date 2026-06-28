from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class SesionCaja(Base):
    __tablename__ = "pos_sesiones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    cajero_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    fecha_apertura = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_cierre = Column(DateTime, nullable=True)
    
    fondo_inicial = Column(Float, default=0.0)
    total_efectivo = Column(Float, default=0.0)
    total_tarjeta = Column(Float, default=0.0)
    diferencia = Column(Float, default=0.0)
    
    estado = Column(String, default="abierta") # abierta, cerrada
    notas = Column(Text, nullable=True)

    cajero = relationship("Usuario", foreign_keys=[cajero_id])

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    razon_social = Column(String, nullable=False)
    rfc = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    direccion = Column(Text, nullable=True)
    limite_credito = Column(Float, default=0.0)
    
    ventas = relationship("VentaPOS", back_populates="cliente")

class VentaPOS(Base):
    __tablename__ = "ventas_pos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    folio = Column(String, index=True, unique=True, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=True) # Puede ser venta al público general
    vendedor_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    sesion_id = Column(String, ForeignKey("pos_sesiones.id"), nullable=True)
    
    subtotal = Column(Float, nullable=False, default=0.0)
    iva = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    
    metodo_pago = Column(String, nullable=False) # EFECTIVO, TARJETA, TRANSFERENCIA
    estado = Column(String, default="completada") # completada, cancelada
    
    notas = Column(Text, nullable=True)
    
    cliente = relationship("Cliente", back_populates="ventas")
    vendedor = relationship("Usuario", foreign_keys=[vendedor_id])
    sesion = relationship("SesionCaja")
    detalles = relationship("DetalleVentaPOS", back_populates="venta", cascade="all, delete-orphan")

class DetalleVentaPOS(Base):
    __tablename__ = "detalles_venta_pos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    venta_id = Column(String, ForeignKey("ventas_pos.id"), nullable=False)
    lote_id = Column(String, ForeignKey("inv_lotes.id"), nullable=False)
    
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False) # cantidad * precio_unitario
    
    venta = relationship("VentaPOS", back_populates="detalles")
    lote = relationship("LoteProducto")

class OrdenVenta(Base):
    __tablename__ = "ventas_ordenes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    folio = Column(String, index=True, unique=True, nullable=False)
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_validez = Column(DateTime, nullable=True) # Vigencia de la cotización
    
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    
    estado = Column(String, default="borrador") # borrador (cotización), confirmada (orden), facturada, cancelada
    
    subtotal = Column(Float, nullable=False, default=0.0)
    iva = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    
    notas = Column(Text, nullable=True)
    terminos_pago = Column(String, nullable=True)
    
    cliente = relationship("Cliente")
    vendedor = relationship("Usuario", foreign_keys=[vendedor_id])
    detalles = relationship("DetalleOrdenVenta", back_populates="orden", cascade="all, delete-orphan")

class DetalleOrdenVenta(Base):
    __tablename__ = "detalles_orden_venta"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    orden_id = Column(String, ForeignKey("ventas_ordenes.id"), nullable=False)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    descuento_porcentaje = Column(Float, default=0.0)
    subtotal = Column(Float, nullable=False)
    
    orden = relationship("OrdenVenta", back_populates="detalles")
    producto = relationship("ProductoTextil")

class ConfiguracionVenta(Base):
    __tablename__ = "ventas_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, unique=True, nullable=False)
    
    encabezado_ticket = Column(Text, nullable=True, default="Guayabera ERP - ¡Gracias por su compra!")
    pie_ticket = Column(Text, nullable=True, default="Conserve su ticket para cambios o devoluciones.")
    permite_credito = Column(Boolean, default=True)
    metodos_pago_permitidos = Column(String, default="EFECTIVO,TARJETA,TRANSFERENCIA,CRÉDITO")
    equipos_ventas = Column(Text, default="[]") # JSON con los equipos de ventas
