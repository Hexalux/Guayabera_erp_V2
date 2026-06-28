from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class CategoriaProductoTextil(Base):
    """Categorías de productos textiles (telas, avíos, etc.)"""
    __tablename__ = "inv_categorias"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(100), nullable=False)
    codigo: str = Column(String(50), unique=True, nullable=False, index=True)
    descripcion: str = Column(Text, nullable=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    # Jerarquía
    parent_id: str = Column(String, ForeignKey("inv_categorias.id"), nullable=True)
    
    # Metadatos
    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    parent = relationship("CategoriaProductoTextil", remote_side=[id], backref="subcategorias")
    productos = relationship("ProductoTextil", back_populates="categoria")

class UnidadMedida(Base):
    """Unidades de medida (metros, piezas, kilogramos)"""
    __tablename__ = "inv_unidades_medida"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    nombre: str = Column(String(50), nullable=False) # "Metros", "Piezas"
    abreviatura: str = Column(String(10), nullable=False) # "m", "pz"
    
    is_active: bool = Column(Boolean, default=True)


class ProductoTextil(Base):
    """Productos textiles con control de inventario y atributos"""
    __tablename__ = "inv_productos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(150), nullable=False, index=True)
    sku: str = Column(String(100), unique=True, nullable=False, index=True)
    categoria_id: str = Column(String, ForeignKey("inv_categorias.id"), nullable=False)
    unidad_medida_id: str = Column(String, ForeignKey("inv_unidades_medida.id"), nullable=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    # Atributos específicos textiles
    tipo_producto: str = Column(String(50), default="producto_terminado")  # "tela", "avio", "insumo", "producto_terminado"
    composicion: str = Column(String(100), nullable=True)  # lino, algodón, etc.
    gramaje: float = Column(Numeric(8, 2), nullable=True)  # g/m2
    ancho: float = Column(Numeric(8, 2), nullable=True)  # cm
    color_pantone: str = Column(String(50), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    categoria = relationship("CategoriaProductoTextil", back_populates="productos")
    unidad_medida = relationship("UnidadMedida")
    lotes = relationship("LoteProducto", back_populates="producto")


class Almacen(Base):
    """Almacenes de la empresa"""
    __tablename__ = "inv_almacenes"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(100), nullable=False)
    codigo: str = Column(String(20), unique=True, nullable=False, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ubicaciones = relationship("UbicacionAlmacen", back_populates="almacen")


class UbicacionAlmacen(Base):
    """Ubicaciones jerárquicas dentro de un almacén (pasillos, estantes, racks, niveles) al estilo Odoo"""
    __tablename__ = "inv_ubicaciones"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    almacen_id: str = Column(String, ForeignKey("inv_almacenes.id"), nullable=False)
    nombre: str = Column(String(100), nullable=False)  # Ej. "Pasillo A - Estante 2 - Rack 3"
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    # Jerarquía recursiva
    parent_id: str = Column(String, ForeignKey("inv_ubicaciones.id"), nullable=True)

    # Odoo Style Grid Coordinates
    pasillo: str = Column(String(50), nullable=True)
    estante: str = Column(String(50), nullable=True)
    rack: str = Column(String(50), nullable=True)
    nivel: str = Column(String(50), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    almacen = relationship("Almacen", back_populates="ubicaciones")
    parent = relationship("UbicacionAlmacen", remote_side=[id], backref="sub_ubicaciones")


class LoteProducto(Base):
    """Lotes de productos con trazabilidad y variaciones"""
    __tablename__ = "inv_lotes"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    producto_id: str = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    numero_lote: str = Column(String(100), nullable=False, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    # Ubicación Odoo Style
    ubicacion_id: str = Column(String, ForeignKey("inv_ubicaciones.id"), nullable=True)
    cantidad: float = Column(Numeric(12, 2), default=0.00)

    # Control de tono
    variacion_tono: str = Column(String(100), nullable=True)  # Importante en textiles
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    producto = relationship("ProductoTextil", back_populates="lotes")
    ubicacion = relationship("UbicacionAlmacen")


class MovimientoInventario(Base):
    """Trazabilidad completa de movimientos de stock origen -> destino"""
    __tablename__ = "inv_movimientos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    lote_id: str = Column(String, ForeignKey("inv_lotes.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    # Ubicaciones de trazabilidad
    ubicacion_origen_id: str = Column(String, ForeignKey("inv_ubicaciones.id"), nullable=True)
    ubicacion_destino_id: str = Column(String, ForeignKey("inv_ubicaciones.id"), nullable=True)
    
    cantidad: float = Column(Numeric(12, 2), nullable=False)
    tipo_movimiento: str = Column(String(50), nullable=False)  # "entrada", "salida", "transferencia", "ajuste"
    referencia: str = Column(String(100), nullable=True)  # Ej. Orden de Producción OP-001, Venta V-102
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lote = relationship("LoteProducto")
    ubicacion_origen = relationship("UbicacionAlmacen", foreign_keys=[ubicacion_origen_id])
    ubicacion_destino = relationship("UbicacionAlmacen", foreign_keys=[ubicacion_destino_id])
