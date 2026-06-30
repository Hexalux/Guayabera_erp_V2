
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class EstadoOrden(enum.Enum):
    PENDIENTE = "pendiente"
    CORTE = "corte"
    COSTURA = "costura"
    ACABADO = "acabado"
    TERMINADO = "terminado"

class OrdenProduccion(Base):
    __tablename__ = "ordenes_produccion"
    id = Column(Integer, primary_key=True, index=True)
    numero_orden = Column(String(50), unique=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer)
    estado = Column(SQLEnum(EstadoOrden), default=EstadoOrden.PENDIENTE)
    fecha_entrega = Column(DateTime)
    bom_id = Column(Integer, ForeignKey("listas_materiales.id"))
    creado_en = Column(DateTime, default=datetime.utcnow)

class ListaMateriales(Base): # BOM
    __tablename__ = "listas_materiales"
    id = Column(Integer, primary_key=True, index=True)
    producto_padre_id = Column(Integer, ForeignKey("productos.id"))
    version = Column(String(10))
    items = relationship("BOMItem", back_populates="lista")

class BOMItem(Base):
    __tablename__ = "bom_items"
    id = Column(Integer, primary_key=True, index=True)
    lista_id = Column(Integer, ForeignKey("listas_materiales.id"))
    material_id = Column(Integer, ForeignKey("productos.id"))
    cantidad_requerida = Column(Float)
    unidad_medida = Column(String(20))
    merma_estimada = Column(Float, default=0.0)
    lista = relationship("ListaMateriales", back_populates="items")

class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    tipo = Column(String(20)) # entrada, salida, ajuste
    cantidad = Column(Float)
    ubicacion_origen = Column(String(50))
    ubicacion_destino = Column(String(50))
    referencia = Column(String(100))
    contabilizado = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, nullable=True)
