from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenants, users, operaciones_filiales, licencias, admin, tenant_portal

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
