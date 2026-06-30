
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ProductoTextil(Base):
    __tablename__ = "productos_textiles"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    gramaje_gsm = Column(Float)
    factor_conversion = Column(Float) # Kg a Piezas
    pantone_code = Column(String(20))
    requiere_lote_tinte = Column(Boolean, default=True)

class LoteTintoreria(Base):
    __tablename__ = "lotes_tintoreria"
    id = Column(Integer, primary_key=True, index=True)
    codigo_lote = Column(String(50), unique=True)
    color_formula = Column(String(100))
    stock_restante_kg = Column(Float)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

class RegistroDestajo(Base):
    __tablename__ = "registros_destajo"
    id = Column(Integer, primary_key=True, index=True)
    operario_id = Column(Integer, ForeignKey("empleados.id"))
    operacion = Column(String(100))
    piezas_buenas = Column(Integer)
    piezas_malas = Column(Integer)
    tarifa_unitaria = Column(Float)
    fecha = Column(DateTime, default=datetime.utcnow)
