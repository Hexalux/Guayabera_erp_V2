
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from datetime import datetime
from app.core.database import Base

class CFDI(Base):
    __tablename__ = "cfdi_comprobantes"
    id = Column(Integer, primary_key=True, index=True)
    uuid_fiscal = Column(String(36), unique=True, nullable=True)
    folio = Column(String(50))
    serie = Column(String(10))
    tipo = Column(String(10)) # I=Egreso, P=Ingreso
    rfc_emisor = Column(String(13))
    rfc_receptor = Column(String(13))
    total = Column(Float)
    xml_original = Column(Text)
    xml_timbrado = Column(Text)
    estado_sat = Column(String(20), default="vigente")
    fecha_timbrado = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
