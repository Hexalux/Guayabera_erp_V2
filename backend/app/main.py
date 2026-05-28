from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db
from app.middleware.tenant_middleware import TenantMiddleware


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Contexto de vida de la aplicación"""
    logger.info("Inicializando la base de datos...")
    await init_db()
    yield
    logger.info("Aplicación cerrada")


# Inicializar la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Agregar middleware para soporte multitenant
app.add_middleware(TenantMiddleware)

# Agregar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if hasattr(settings, 'BACKEND_CORS_ORIGINS') else ["*"], # Asegurar que exista el atributo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Agregar router de autenticación
security = HTTPBearer()


@app.get("/")
async def root():
    """
    Endpoint raíz para verificar que la API está funcionando
    """
    return {"message": "Guayabera ERP Suite v2.0 - API Funcionando"}


@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de salud de la aplicación
    """
    return {
        "status": "healthy",
        "service": "guayabera-erp-v2-backend",
        "version": "2.0.0"
    }


# Incluir routers de la API
app.include_router(api_router, prefix=settings.API_V1_STR)


# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: object, exc: Exception):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ha ocurrido un error interno en el servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
