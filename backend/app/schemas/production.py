from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# ==========================================
# RECETAS DE PRODUCCIÓN (BOM)
# ==========================================
class RecetaProduccionBase(BaseModel):
    producto_padre_id: str
    insumo_id: str
    cantidad_requerida: float

class RecetaProduccionCreate(RecetaProduccionBase):
    tenant_id: Optional[str] = None

class RecetaProduccionResponse(RecetaProduccionBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# COSTOS MAQUILA
# ==========================================
class CostoSubcontratacionMaquilaBase(BaseModel):
    orden_produccion_id: str
    maquilador_nombre: str
    costo_servicio: float
    piezas_enviadas: int
    piezas_recibidas: Optional[int] = 0
    referencia_factura: Optional[str] = None

class CostoSubcontratacionMaquilaCreate(CostoSubcontratacionMaquilaBase):
    tenant_id: Optional[str] = None

class CostoSubcontratacionMaquilaResponse(CostoSubcontratacionMaquilaBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# ÓRDENES DE PRODUCCIÓN
# ==========================================
class OrdenProduccionBase(BaseModel):
    folio: str
    producto_final_id: str
    cantidad_programada: float
    cantidad_producida: Optional[float] = 0.0
    estado: Optional[str] = "borrador" # borrador, en_proceso, maquila, completado, cancelado
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    costo_materia_prima: Optional[float] = 0.0
    costo_maquila_externa: Optional[float] = 0.0
    costo_total: Optional[float] = 0.0

class OrdenProduccionCreate(OrdenProduccionBase):
    tenant_id: Optional[str] = None

class OrdenProduccionResponse(OrdenProduccionBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Modelo auxiliar para finalizar la orden recibiendo los costos finales y mermas declaradas
class FinalizarOrdenRequest(BaseModel):
    cantidad_real_producida: float
    costo_maquila_adicional: Optional[float] = 0.0
    maquilador_nombre: Optional[str] = "Producción Interna"

# ==========================================
# PROYECTOS DE PRODUCCIÓN
# ==========================================
class ProyectoProduccionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    estado: str = "planificacion"
    fecha_inicio: Optional[date] = None
    fecha_entrega: Optional[date] = None
    responsable_id: Optional[str] = None

class ProyectoProduccionCreate(ProyectoProduccionBase):
    pass

class ProyectoProduccionResponse(ProyectoProduccionBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
