from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class CotizacionVenta(Base):
    __tablename__ = "b2b_cotizaciones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    folio = Column(String, nullable=False, unique=True)
    
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_vigencia = Column(DateTime, nullable=False)
    
    subtotal = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    estado = Column(String, default="borrador") # borrador, enviada, aceptada, rechazada
    notas = Column(Text, nullable=True)

    cliente = relationship("Cliente")
    vendedor = relationship("Usuario")
    detalles = relationship("DetalleCotizacion", back_populates="cotizacion", cascade="all, delete-orphan")
    pedido = relationship("PedidoVenta", back_populates="cotizacion", uselist=False)

class DetalleCotizacion(Base):
    __tablename__ = "b2b_detalles_cotizacion"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    cotizacion_id = Column(String, ForeignKey("b2b_cotizaciones.id"), nullable=False)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    cotizacion = relationship("CotizacionVenta", back_populates="detalles")
    producto = relationship("ProductoTextil")


class PedidoVenta(Base):
    __tablename__ = "b2b_pedidos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    folio = Column(String, nullable=False, unique=True)
    
    cotizacion_id = Column(String, ForeignKey("b2b_cotizaciones.id"), nullable=True)
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    
    fecha_pedido = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_entrega_esperada = Column(DateTime, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    estado = Column(String, default="confirmado") # confirmado, remisionado_parcial, remisionado_total, cancelado
    notas = Column(Text, nullable=True)

    cliente = relationship("Cliente")
    vendedor = relationship("Usuario")
    cotizacion = relationship("CotizacionVenta", back_populates="pedido")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    remisiones = relationship("RemisionVenta", back_populates="pedido")


class DetallePedido(Base):
    __tablename__ = "b2b_detalles_pedido"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    pedido_id = Column(String, ForeignKey("b2b_pedidos.id"), nullable=False)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    cantidad_solicitada = Column(Integer, nullable=False)
    cantidad_remisionada = Column(Integer, default=0)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    pedido = relationship("PedidoVenta", back_populates="detalles")
    producto = relationship("ProductoTextil")


class RemisionVenta(Base):
    __tablename__ = "b2b_remisiones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    folio = Column(String, nullable=False, unique=True)
    
    pedido_id = Column(String, ForeignKey("b2b_pedidos.id"), nullable=True)
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    subtotal = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    estado = Column(String, default="emitida") # emitida, facturada, cancelada
    
    cuenta_por_cobrar_id = Column(String, ForeignKey("cuentas_por_cobrar.id"), nullable=True)
    poliza_id = Column(String, ForeignKey("cont_polizas.id"), nullable=True)

    cliente = relationship("Cliente")
    vendedor = relationship("Usuario")
    pedido = relationship("PedidoVenta", back_populates="remisiones")
    detalles = relationship("DetalleRemision", back_populates="remision", cascade="all, delete-orphan")


class DetalleRemision(Base):
    __tablename__ = "b2b_detalles_remision"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    remision_id = Column(String, ForeignKey("b2b_remisiones.id"), nullable=False)
    detalle_pedido_id = Column(String, ForeignKey("b2b_detalles_pedido.id"), nullable=True)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    remision = relationship("RemisionVenta", back_populates="detalles")
    producto = relationship("ProductoTextil")
