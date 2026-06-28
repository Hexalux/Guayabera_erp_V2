from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenants, users, operaciones_filiales, licencias, admin, tenant_portal, modulos, finance, inventory, production, sales, purchases, treasury, cxc, expenses, sales_b2b, accounting, hr
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

# Rutas para los módulos ported (Inventory, Finance, HR, Production, Branches, CAD)
api_router.include_router(modulos.router, prefix="", tags=["business-modules"])

# Módulo Contable (Finance)
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])

# Módulo de Inventario (Inventory)
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])

# Módulo de Producción (MRP)
api_router.include_router(production.router, prefix="/production", tags=["production"])

# Módulo de Ventas (Sales)
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])

# Módulo de Compras (Purchases)
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])

# Módulo de Tesorería (Treasury)
api_router.include_router(treasury.router, prefix="/treasury", tags=["treasury"])

# Módulo de Cuentas por Cobrar (CxC)
api_router.include_router(cxc.router, prefix="/cxc", tags=["cxc"])

# Módulo de Control de Gastos
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])

# Cadena de Suministro B2B
api_router.include_router(sales_b2b.router, prefix="/sales-b2b", tags=["sales_b2b"])

# Contabilidad y Reportes Financieros
api_router.include_router(accounting.router, prefix="/accounting", tags=["accounting"])

# Módulo de Recursos Humanos (HR)
api_router.include_router(hr.router, prefix="/hr", tags=["hr"])
