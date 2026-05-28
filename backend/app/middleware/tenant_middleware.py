from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from contextvars import ContextVar

from app.core.database import engine
from app.models.tenant import Tenant
from app.core.config import settings

logger = logging.getLogger(__name__)

# Context variable para almacenar el tenant actual
current_tenant: ContextVar[Tenant] = ContextVar("current_tenant", default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware para identificar y validar el tenant actual en cada solicitud
    """
    async def dispatch(self, request: Request, call_next):
        # Obtener el identificador del tenant de los headers
        tenant_id = request.headers.get(settings.TENANT_IDENTIFICATION_HEADER)
        
        # Si no se proporciona un tenant_id y el usuario no es superusuario, lanzar error
        if not tenant_id:
            # Aquí podríamos verificar si es superusuario antes de lanzar error
            # Por ahora, dejamos pasar sin tenant para permitir autenticación
            request.state.tenant = None
        else:
            # Buscar el tenant en la base de datos
            async with AsyncSession(engine) as session:
                result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
                tenant = result.scalars().first()
                
                if not tenant or not tenant.is_active:
                    raise HTTPException(status_code=404, detail="Tenant no encontrado o inactivo")
                
                # Almacenar el tenant en la variable de contexto
                current_tenant.set(tenant)
                request.state.tenant = tenant
        
        response = await call_next(request)
        return response