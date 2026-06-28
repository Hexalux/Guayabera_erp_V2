from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    razon_social = Column(String, nullable=False)
    rfc = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    dias_credito = Column(Float, default=0.0)
    activo = Column(Boolean, default=True)

    listas_precio = relationship("ListaPrecioProveedor", back_populates="proveedor", cascade="all, delete-orphan")

class ListaPrecioProveedor(Base):
    __tablename__ = "prov_listas_precio"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=False)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    codigo_proveedor = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
    moneda = Column(String, default="MXN")
    factor_conversion = Column(Float, default=1.0)
    
    proveedor = relationship("Proveedor", back_populates="listas_precio")
    producto = relationship("ProductoTextil")

class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    folio = Column(String, index=True, unique=True, nullable=False)
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_recepcion = Column(DateTime, nullable=True)
    
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=False)
    comprador_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    
    estado = Column(String, default="rfq") # rfq, emitida, recibida, cancelada
    
    subtotal = Column(Float, nullable=False, default=0.0)
    iva = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    
    notas = Column(Text, nullable=True)
    
    proveedor = relationship("Proveedor")
    comprador = relationship("Usuario")
    detalles = relationship("DetalleOrdenCompra", back_populates="orden", cascade="all, delete-orphan")
    cuenta_por_pagar = relationship("CuentaPorPagar", back_populates="orden_compra", uselist=False)

class DetalleOrdenCompra(Base):
    __tablename__ = "detalles_orden_compra"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    orden_id = Column(String, ForeignKey("ordenes_compra.id"), nullable=False)
    producto_textil_id = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    
    cantidad_solicitada = Column(Float, nullable=False)
    cantidad_recibida = Column(Float, default=0.0)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    orden = relationship("OrdenCompra", back_populates="detalles")
    producto = relationship("ProductoTextil")

class CuentaPorPagar(Base):
    __tablename__ = "cuentas_por_pagar"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    orden_compra_id = Column(String, ForeignKey("ordenes_compra.id"), nullable=False)
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=False)
    
    monto_original = Column(Float, nullable=False)
    monto_pagado = Column(Float, default=0.0)
    saldo_pendiente = Column(Float, nullable=False)
    
    fecha_emision = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(String, default="pendiente") # pendiente, pagada, parcial
    
    orden_compra = relationship("OrdenCompra", back_populates="cuenta_por_pagar")
    proveedor = relationship("Proveedor")
    pagos = relationship("PagoCxP", back_populates="cuenta_por_pagar")
    notas_credito = relationship("NotaCreditoProveedor", back_populates="cuenta_por_pagar")

class PagoCxP(Base):
    __tablename__ = "pagos_cxp"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    cuenta_por_pagar_id = Column(String, ForeignKey("cuentas_por_pagar.id"), nullable=False)
    transaccion_bancaria_id = Column(String, ForeignKey("transacciones_bancarias.id"), nullable=True) # Egreso en banco
    
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    referencia = Column(String, nullable=True)
    
    cuenta_por_pagar = relationship("CuentaPorPagar", back_populates="pagos")
    transaccion = relationship("TransaccionBancaria")

class NotaCreditoProveedor(Base):
    __tablename__ = "notas_credito_proveedor"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    
    folio = Column(String, index=True, unique=True, nullable=False)
    cuenta_por_pagar_id = Column(String, ForeignKey("cuentas_por_pagar.id"), nullable=False)
    
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    concepto = Column(Text, nullable=False)
    
    poliza_id = Column(String, ForeignKey("cont_polizas.id"), nullable=True)
    
    cuenta_por_pagar = relationship("CuentaPorPagar", back_populates="notas_credito")
