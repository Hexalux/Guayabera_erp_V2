from datetime import datetime, timedelta
import secrets
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.admin import Admin
from app.models.licencia import Licencia, TipoLicencia
from app.models.tenant import Tenant
from app.models.usuario import Usuario

router = APIRouter()


class SolicitudLicenciaRequest(BaseModel):
    tipo_licencia_id: str
    notas: Optional[str] = None


class TenantUserCreateRequest(BaseModel):
    email: str
    nombre_completo: Optional[str] = None
    password: str
    tipo_usuario: str = "normal"


def generar_codigo_solicitud(longitud: int = 12) -> str:
    caracteres = string.ascii_uppercase + string.digits
    return "SOL-" + "".join(secrets.choice(caracteres) for _ in range(longitud))


def licencia_to_dict(licencia: Licencia, tipo: Optional[TipoLicencia] = None):
    return {
        "id": licencia.id,
        "tenant_id": licencia.tenant_id,
        "tipo_licencia_id": licencia.tipo_licencia_id,
        "tipo_licencia_nombre": tipo.nombre if tipo else None,
        "codigo": licencia.codigo,
        "fecha_inicio": licencia.fecha_inicio,
        "fecha_fin": licencia.fecha_fin,
        "activa": licencia.activa,
        "usada": licencia.usada,
        "notas": licencia.notas,
        "created_at": licencia.created_at,
    }


async def get_current_tenant_context(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no pertenece a un tenant",
        )

    stmt = select(Tenant).where(cast(Tenant.id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado",
        )

    return current_user, tenant


@router.get("/resumen")
async def obtener_resumen_tenant(
    context=Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Resumen operativo del tenant autenticado: licencia activa, licencias, usuarios y empresas filiales.
    """
    current_user, tenant = context
    now = datetime.utcnow()

    licencias_result = await db.execute(
        select(Licencia, TipoLicencia)
        .join(TipoLicencia, Licencia.tipo_licencia_id == TipoLicencia.id)
        .where(cast(Licencia.tenant_id, String) == str(tenant.id))
        .order_by(Licencia.fecha_inicio.desc())
    )
    licencias_rows = licencias_result.all()
    licencias = [licencia_to_dict(licencia, tipo) for licencia, tipo in licencias_rows]
    licencia_activa = next(
        (
            licencia_to_dict(licencia, tipo)
            for licencia, tipo in licencias_rows
            if licencia.activa and licencia.fecha_fin and licencia.fecha_fin.replace(tzinfo=None) > now
        ),
        None,
    )

    usuarios_result = await db.execute(
        select(Usuario).where(cast(Usuario.tenant_id, String) == str(tenant.id)).order_by(Usuario.created_at.desc())
    )
    usuarios = usuarios_result.scalars().all()

    empresas = []
    if tenant.es_grupo_corporativo:
        filiales_result = await db.execute(
            select(Tenant).where(cast(Tenant.grupo_corporativo_id, String) == str(tenant.id))
        )
        empresas = filiales_result.scalars().all()

    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "contact_email": tenant.contact_email,
            "contact_phone": tenant.contact_phone,
            "descripcion": tenant.descripcion,
            "is_active": tenant.is_active,
            "es_grupo_corporativo": tenant.es_grupo_corporativo,
        },
        "current_user": {
            "id": current_user.id,
            "email": current_user.email,
            "nombre_completo": current_user.nombre_completo,
            "tipo_usuario": current_user.tipo_usuario,
        },
        "licencia_activa": licencia_activa,
        "licencias": licencias,
        "usuarios": [
            {
                "id": usuario.id,
                "email": usuario.email,
                "nombre_completo": usuario.nombre_completo,
                "tipo_usuario": usuario.tipo_usuario,
                "is_active": usuario.is_active,
                "created_at": usuario.created_at,
            }
            for usuario in usuarios
        ],
        "empresas": [
            {
                "id": empresa.id,
                "name": empresa.name,
                "subdomain": empresa.subdomain,
                "contact_email": empresa.contact_email,
                "contact_phone": empresa.contact_phone,
                "descripcion": empresa.descripcion,
                "is_active": empresa.is_active,
            }
            for empresa in empresas
        ],
        "modulos": [
            {"key": "licencias", "nombre": "Licencias", "habilitado": True},
            {"key": "usuarios", "nombre": "Usuarios", "habilitado": True},
            {"key": "empresas", "nombre": "Empresas", "habilitado": tenant.es_grupo_corporativo},
            {"key": "rh", "nombre": "Recursos Humanos", "habilitado": False},
        ],
    }


@router.get("/tipos-licencia")
async def listar_tipos_licencia(
    context=Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TipoLicencia).order_by(TipoLicencia.precio.asc()))
    tipos = result.scalars().all()

    return {
        "tipos_licencia": [
            {
                "id": tipo.id,
                "nombre": tipo.nombre,
                "descripcion": tipo.descripcion,
                "duracion_dias": tipo.duracion_dias,
                "precio": tipo.precio,
                "es_prueba": tipo.es_prueba,
            }
            for tipo in tipos
        ]
    }


@router.post("/solicitar-licencia", status_code=status.HTTP_201_CREATED)
async def solicitar_licencia(
    solicitud: SolicitudLicenciaRequest,
    context=Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una solicitud de licencia del tenant. Queda inactiva para aprobacion del super-admin.
    """
    current_user, tenant = context

    tipo_result = await db.execute(
        select(TipoLicencia).where(cast(TipoLicencia.id, String) == solicitud.tipo_licencia_id)
    )
    tipo = tipo_result.scalar_one_or_none()

    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de licencia no encontrado",
        )

    fecha_inicio = datetime.utcnow()
    nueva_licencia = Licencia(
        tenant_id=tenant.id,
        tipo_licencia_id=tipo.id,
        codigo=generar_codigo_solicitud(),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_inicio + timedelta(days=tipo.duracion_dias),
        activa=False,
        usada=False,
        notas=f"Solicitud pendiente creada por {current_user.email}. {solicitud.notas or ''}".strip(),
    )

    db.add(nueva_licencia)
    await db.commit()
    await db.refresh(nueva_licencia)

    return {
        "mensaje": "Solicitud de licencia registrada. Queda pendiente de aprobacion del super-admin.",
        "licencia": licencia_to_dict(nueva_licencia, tipo),
    }


@router.get("/usuarios")
async def listar_usuarios_tenant(
    context=Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    current_user, tenant = context

    if current_user.tipo_usuario not in ["admin_empresa", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador del tenant puede gestionar usuarios",
        )

    result = await db.execute(
        select(Usuario).where(cast(Usuario.tenant_id, String) == str(tenant.id)).order_by(Usuario.created_at.desc())
    )
    usuarios = result.scalars().all()

    return {
        "usuarios": [
            {
                "id": usuario.id,
                "email": usuario.email,
                "nombre_completo": usuario.nombre_completo,
                "tipo_usuario": usuario.tipo_usuario,
                "tenant_id": usuario.tenant_id,
                "is_active": usuario.is_active,
            }
            for usuario in usuarios
        ]
    }


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def crear_usuario_tenant(
    user_data: TenantUserCreateRequest,
    context=Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    current_user, tenant = context

    if current_user.tipo_usuario not in ["admin_empresa", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador del tenant puede crear usuarios",
        )

    if user_data.tipo_usuario not in ["normal", "admin_empresa"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de usuario no permitido para tenant",
        )

    existing_user_result = await db.execute(select(Usuario).where(Usuario.email == user_data.email))
    existing_admin_result = await db.execute(select(Admin).where(Admin.email == user_data.email))

    if existing_user_result.scalar_one_or_none() or existing_admin_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    nuevo_usuario = Usuario(
        email=user_data.email,
        nombre_completo=user_data.nombre_completo,
        hashed_password=get_password_hash(user_data.password),
        tipo_usuario=user_data.tipo_usuario,
        tenant_id=tenant.id,
        is_active=True,
    )

    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)

    return {
        "mensaje": "Usuario creado exitosamente",
        "usuario": {
            "id": nuevo_usuario.id,
            "email": nuevo_usuario.email,
            "nombre_completo": nuevo_usuario.nombre_completo,
            "tipo_usuario": nuevo_usuario.tipo_usuario,
            "tenant_id": nuevo_usuario.tenant_id,
            "is_active": nuevo_usuario.is_active,
        }
    }
