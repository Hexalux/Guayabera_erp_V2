from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class OrdenProduccion(Base):
    """Órdenes de producción textil"""
    __tablename__ = "mrp_ordenes_produccion"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    folio: str = Column(String(50), unique=True, nullable=False, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    producto_final_id: str = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    cantidad_programada: float = Column(Numeric(12, 2), nullable=False)
    cantidad_producida: float = Column(Numeric(12, 2), default=0.00)
    
    estado: str = Column(String(50), default="borrador")  # borrador, en_proceso, maquila, completado, cancelado
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)

    # Costos imputados
    costo_materia_prima: float = Column(Numeric(12, 2), default=0.00)
    costo_maquila_externa: float = Column(Numeric(12, 2), default=0.00)
    costo_total: float = Column(Numeric(12, 2), default=0.00)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    producto_final = relationship("ProductoTextil")
    costos_maquila = relationship("CostoSubcontratacionMaquila", back_populates="orden_produccion")


class RecetaProduccion(Base):
    """Lista de materiales (BOM) para cada diseño de guayabera"""
    __tablename__ = "mrp_bom"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    producto_padre_id: str = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    insumo_id: str = Column(String, ForeignKey("inv_productos.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    cantidad_requerida: float = Column(Numeric(12, 4), nullable=False)  # Ej. 1.8 metros de tela por guayabera

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto_padre = relationship("ProductoTextil", foreign_keys=[producto_padre_id])
    insumo = relationship("ProductoTextil", foreign_keys=[insumo_id])


class CostoSubcontratacionMaquila(Base):
    """Registro de costos de talleres de costura / maquiladores externos"""
    __tablename__ = "mrp_maquila_costos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    orden_produccion_id: str = Column(String, ForeignKey("mrp_ordenes_produccion.id"), nullable=False)
    maquilador_nombre: str = Column(String(200), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    costo_servicio: float = Column(Numeric(12, 2), nullable=False)
    piezas_enviadas: int = Column(Integer, nullable=False)
    piezas_recibidas: int = Column(Integer, default=0)
    referencia_factura: str = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orden_produccion = relationship("OrdenProduccion", back_populates="costos_maquila")


class ProyectoProduccion(Base):
    """Proyectos que agrupan y organizan varias órdenes de producción (Kanban)"""
    __tablename__ = "mrp_proyectos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    nombre: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=True)
    
    estado: str = Column(String(50), default="planificacion") # planificacion, diseno, corte, maquila, terminado
    
    fecha_inicio = Column(Date, nullable=True)
    fecha_entrega = Column(Date, nullable=True)
    
    responsable_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    responsable = relationship("Usuario")
