from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# CATEGORÍAS
# ==========================================
class CategoriaProductoTextilBase(BaseModel):
    nombre: str
    codigo: str
    descripcion: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = True

class CategoriaProductoTextilCreate(CategoriaProductoTextilBase):
    tenant_id: Optional[str] = None

class CategoriaProductoTextilResponse(CategoriaProductoTextilBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# UNIDADES DE MEDIDA
# ==========================================
class UnidadMedidaBase(BaseModel):
    nombre: str
    abreviatura: str
    is_active: Optional[bool] = True

class UnidadMedidaCreate(UnidadMedidaBase):
    tenant_id: Optional[str] = None

class UnidadMedidaResponse(UnidadMedidaBase):
    id: str
    tenant_id: Optional[str]
    class Config:
        from_attributes = True

# ==========================================
# PRODUCTOS
# ==========================================
class ProductoTextilBase(BaseModel):
    nombre: str
    sku: str
    categoria_id: str
    unidad_medida_id: Optional[str] = None
    tipo_producto: Optional[str] = "producto_terminado"
    composicion: Optional[str] = None
    gramaje: Optional[float] = None
    ancho: Optional[float] = None
    color_pantone: Optional[str] = None
    is_active: Optional[bool] = True

class ProductoTextilCreate(ProductoTextilBase):
    tenant_id: Optional[str] = None

class ProductoTextilResponse(ProductoTextilBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# ALMACENES Y UBICACIONES
# ==========================================
class AlmacenBase(BaseModel):
    nombre: str
    codigo: str
    is_active: Optional[bool] = True

class AlmacenCreate(AlmacenBase):
    tenant_id: Optional[str] = None

class AlmacenResponse(AlmacenBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class UbicacionAlmacenBase(BaseModel):
    almacen_id: str
    nombre: str
    parent_id: Optional[str] = None
    pasillo: Optional[str] = None
    estante: Optional[str] = None
    rack: Optional[str] = None
    nivel: Optional[str] = None
    is_active: Optional[bool] = True

class UbicacionAlmacenCreate(UbicacionAlmacenBase):
    tenant_id: Optional[str] = None

class UbicacionAlmacenResponse(UbicacionAlmacenBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ==========================================
# LOTES Y MOVIMIENTOS
# ==========================================
class LoteProductoBase(BaseModel):
    producto_id: str
    numero_lote: str
    ubicacion_id: Optional[str] = None
    cantidad: float = 0.0
    variacion_tono: Optional[str] = None

class LoteProductoCreate(LoteProductoBase):
    tenant_id: Optional[str] = None

class LoteProductoResponse(LoteProductoBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class MovimientoInventarioBase(BaseModel):
    lote_id: str
    ubicacion_origen_id: Optional[str] = None
    ubicacion_destino_id: Optional[str] = None
    cantidad: float
    tipo_movimiento: str # "entrada", "salida", "transferencia", "ajuste"
    referencia: Optional[str] = None

class MovimientoInventarioCreate(MovimientoInventarioBase):
    tenant_id: Optional[str] = None

class MovimientoInventarioResponse(MovimientoInventarioBase):
    id: str
    tenant_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
