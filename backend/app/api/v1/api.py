from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenants, users, operaciones_filiales, licencias, admin, tenant_portal, contabilidad, terceros, cxc, cxp, gastos, revaluacion
from app.api.v1.endpoints.tesoreria import caja
from app.api.v1.endpoints.finanzas import banco

api_router = APIRouter()

# Rutas de autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Rutas de administración (solo para superadmin)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Rutas de tenants
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])

# Rutas de usuarios
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Rutas de operaciones entre empresas filiales
api_router.include_router(operaciones_filiales.router, prefix="/operaciones-filiales", tags=["operaciones-filiales"])

# Rutas de licencias
api_router.include_router(licencias.router, prefix="/licencias", tags=["licencias"])

# Rutas operativas del tenant autenticado
api_router.include_router(tenant_portal.router, prefix="/tenant-portal", tags=["tenant-portal"])

# Rutas de contabilidad (Sprint 1 - Implementado)
api_router.include_router(contabilidad.router, prefix="/contabilidad", tags=["contabilidad"])

# Rutas de terceros (Sprint 2 - Implementado)
api_router.include_router(terceros.router, prefix="/terceros", tags=["terceros"])

# Rutas de Cuentas por Cobrar (Sprint 3 - Implementado)
api_router.include_router(cxc.router, prefix="/cxc", tags=["cxc"])

# Rutas de tesorería - Caja (Sprint 5 - Implementado)
api_router.include_router(caja.router, prefix="/tesoreria", tags=["tesorería"])

# Rutas de Cuentas por Pagar (Sprint 4 - Implementado)
api_router.include_router(cxp.router, prefix="/cxp", tags=["cxp"])

# Rutas de Control de Gastos (Sprint 7 - Implementado)
api_router.include_router(gastos.router, prefix="/gastos", tags=["gastos"])

# Rutas de Revaluación Cambiaria (Sprint 8 - Implementado)
api_router.include_router(revaluacion.router, prefix="/revaluacion", tags=["revaluacion"])

# Rutas de Bancos (Sprint 6 - Implementado)
api_router.include_router(banco.router, prefix="/bancos", tags=["bancos"])
