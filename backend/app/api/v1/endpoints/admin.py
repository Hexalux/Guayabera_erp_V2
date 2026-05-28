from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import String, cast, select, update
from datetime import datetime, timedelta
import secrets
import string
from typing import List, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.admin import Admin
from app.models.tenant import Tenant, GrupoCorporativo
from app.models.licencia import Licencia, TipoLicencia
from app.models.token import TokenVerificacion
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.schemas.tenant import TenantCreate, TenantUpdate, GrupoCorporativoUpdate
from app.schemas.licencia import LicenciaCreate, LicenciaUpdate
from app.core.security import get_password_hash
from app.api.deps import get_current_admin

router = APIRouter()


class InviteTenantAdminRequest(BaseModel):
    email: str
    tenant_id: str


class CreateCorporationRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class AssignTenantCorporationRequest(BaseModel):
    tenant_id: str
    corporation_id: str


class AssignCorporationTenantsRequest(BaseModel):
    tenant_ids: List[str]


class SuperAdminCreateRequest(BaseModel):
    email: str
    nombre_completo: Optional[str] = None
    password: str


class SuperAdminUpdateRequest(BaseModel):
    email: Optional[str] = None
    nombre_completo: Optional[str] = None
    password: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


def serialize_admin(admin: Admin) -> dict:
    return {
        "id": admin.id,
        "email": admin.email,
        "nombre_completo": admin.nombre_completo,
        "is_verified": admin.is_verified,
        "is_active": admin.is_active,
        "created_at": admin.created_at,
    }

def generar_token_unico(longitud: int = 32) -> str:
    """Genera un token único seguro"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(longitud))

def enviar_invitacion_correo(destinatario: str, asunto: str, cuerpo: str):
    """Función para enviar correos electrónicos de invitación"""
    # Aquí iría la lógica real para enviar correos
    # Por ahora solo imprimimos para simular
    print(f"Invitación enviada a: {destinatario}")
    print(f"Asunto: {asunto}")
    print(f"Cuerpo: {cuerpo}")


@router.get("/super-admins")
async def listar_super_admins(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista los super administradores globales.
    """
    stmt = select(Admin).order_by(Admin.created_at.desc())
    result = await db.execute(stmt)
    admins = result.scalars().all()

    return {
        "super_admins": [
            serialize_admin(admin)
            for admin in admins
        ]
    }


@router.post("/super-admins", status_code=status.HTTP_201_CREATED)
async def crear_super_admin(
    admin_data: SuperAdminCreateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea otro super administrador global. Los tenants no deben crear este tipo de usuario.
    """
    existing_admin_result = await db.execute(select(Admin).where(Admin.email == admin_data.email))
    existing_user_result = await db.execute(select(Usuario).where(Usuario.email == admin_data.email))

    if existing_admin_result.scalar_one_or_none() or existing_user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )

    nuevo_admin = Admin(
        email=admin_data.email,
        nombre_completo=admin_data.nombre_completo,
        hashed_password=get_password_hash(admin_data.password),
        is_verified=True,
        is_active=True,
    )

    db.add(nuevo_admin)
    await db.commit()
    await db.refresh(nuevo_admin)

    return {
        "mensaje": "Super administrador creado exitosamente",
        "admin": serialize_admin(nuevo_admin)
    }


@router.put("/super-admins/{admin_id}")
async def actualizar_super_admin(
    admin_id: str,
    admin_data: SuperAdminUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza datos operativos de un super administrador.
    """
    stmt = select(Admin).where(cast(Admin.id, String) == admin_id)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Super admin no encontrado"
        )

    data = admin_data.model_dump(exclude_unset=True)

    if data.get("email") and data["email"] != admin.email:
        existing_admin_result = await db.execute(
            select(Admin).where(Admin.email == data["email"], cast(Admin.id, String) != admin_id)
        )
        existing_user_result = await db.execute(select(Usuario).where(Usuario.email == data["email"]))

        if existing_admin_result.scalar_one_or_none() or existing_user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email"
            )

    if data.get("is_active") is False and str(current_admin.id) == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio super admin"
        )

    if "password" in data:
        password = data.pop("password")
        if password:
            admin.hashed_password = get_password_hash(password)

    for field, value in data.items():
        setattr(admin, field, value)

    await db.commit()
    await db.refresh(admin)

    return {
        "mensaje": "Super admin actualizado exitosamente",
        "admin": serialize_admin(admin)
    }


@router.put("/super-admins/{admin_id}/desactivar")
async def desactivar_super_admin(
    admin_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    if str(current_admin.id) == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio super admin"
        )

    stmt = select(Admin).where(cast(Admin.id, String) == admin_id)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Super admin no encontrado"
        )

    admin.is_active = False
    await db.commit()

    return {"mensaje": f"Super admin {admin.email} desactivado exitosamente"}


@router.put("/super-admins/{admin_id}/activar")
async def activar_super_admin(
    admin_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Admin).where(cast(Admin.id, String) == admin_id)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Super admin no encontrado"
        )

    admin.is_active = True
    await db.commit()

    return {"mensaje": f"Super admin {admin.email} activado exitosamente"}

@router.post("/crear-tenant")
async def crear_tenant(
    tenant_data: TenantCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para que el superadmin cree nuevos tenants
    """
    # Verificar si ya existe un tenant con el mismo nombre o dominio
    stmt = select(Tenant).where(
        (Tenant.name == tenant_data.name) | (Tenant.subdomain == tenant_data.subdomain)
    )
    result = await db.execute(stmt)
    existing_tenant = result.scalar_one_or_none()
    
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tenant con ese nombre o subdominio"
        )

    if tenant_data.grupo_corporativo_id:
        stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == tenant_data.grupo_corporativo_id)
        result = await db.execute(stmt)
        corporation = result.scalar_one_or_none()

        if not corporation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Corporacion no encontrada"
            )
    
    # Crear el nuevo tenant
    nuevo_tenant = Tenant(
        name=tenant_data.name,
        subdomain=tenant_data.subdomain,
        schema_name=f"tenant_{tenant_data.subdomain}",
        contact_email=tenant_data.contact_email,
        contact_phone=tenant_data.contact_phone,
        descripcion=tenant_data.descripcion,
        grupo_corporativo_id=tenant_data.grupo_corporativo_id,
        is_active=True
    )
    
    db.add(nuevo_tenant)
    await db.commit()
    await db.refresh(nuevo_tenant)
    
    return {
        "mensaje": "Tenant creado exitosamente",
        "tenant_id": nuevo_tenant.id
    }


@router.put("/tenants/{tenant_id}")
async def actualizar_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza datos generales del tenant sin eliminarlo.
    """
    stmt = select(Tenant).where(cast(Tenant.id, String) == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    data = tenant_data.model_dump(exclude_unset=True)

    if data.get("name") or data.get("subdomain"):
        new_name = data.get("name", tenant.name)
        new_subdomain = data.get("subdomain", tenant.subdomain)
        stmt = select(Tenant).where(
            ((Tenant.name == new_name) | (Tenant.subdomain == new_subdomain)),
            cast(Tenant.id, String) != tenant_id
        )
        result = await db.execute(stmt)
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un tenant con ese nombre o subdominio"
            )

    if "grupo_corporativo_id" in data and data["grupo_corporativo_id"]:
        stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == data["grupo_corporativo_id"])
        result = await db.execute(stmt)
        corporation = result.scalar_one_or_none()

        if not corporation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Corporacion no encontrada"
            )

    if "subdomain" in data and "schema_name" not in data:
        data["schema_name"] = f"tenant_{data['subdomain']}"

    for field, value in data.items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    return {
        "mensaje": "Tenant actualizado exitosamente",
        "tenant_id": tenant.id
    }

@router.post("/invitar-tenant-admin")
async def invitar_tenant_admin(
    invite_data: InviteTenantAdminRequest,
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para invitar a un administrador de tenant mediante correo electrónico
    """
    email = invite_data.email
    tenant_id = invite_data.tenant_id

    # Verificar que el tenant existe
    stmt = select(Tenant).where(cast(Tenant.id, String) == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Verificar que no exista un usuario con ese email
    stmt = select(Usuario).where(Usuario.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    
    # Generar token de verificación
    token_verificacion = generar_token_unico()
    expiracion = datetime.utcnow() + timedelta(hours=24)  # El enlace expira en 24 horas
    
    # Guardar el token con referencia al tenant
    nuevo_token = TokenVerificacion(
        tipo_token="invitacion_tenant_admin",
        token=token_verificacion,
        expira_en=expiracion,
        usado=False,
        tenant_id=tenant_id,
        destinatario_email=email
    )
    
    db.add(nuevo_token)
    await db.commit()
    
    # Enviar correo con el enlace de verificación
    enlace_verificacion = f"{settings.FRONTEND_URL}/crear-cuenta/{token_verificacion}"
    cuerpo_correo = f"""
    Hola,
    
    Ha sido invitado como administrador del tenant "{tenant.name}" en Guayabera ERP Suite.
    
    Por favor haga clic en el siguiente enlace para crear su contraseña y activar su cuenta:
    {enlace_verificacion}
    
    Este enlace es válido por 24 horas. Si no solicitó este registro, puede ignorar este mensaje.
    
    Saludos,
    Equipo de Guayabera ERP Suite
    """
    
    # Enviar correo en segundo plano
    background_tasks.add_task(
        enviar_invitacion_correo,
        email,
        "Invitación como Administrador de Tenant - Guayabera ERP Suite",
        cuerpo_correo
    )
    
    return {
        "mensaje": "Invitación enviada exitosamente",
        "expiracion_token": expiracion.isoformat()
    }

@router.post("/crear-corporacion")
async def crear_corporacion(
    corporation_data: CreateCorporationRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear una corporación que agrupa varios tenants
    """
    # Verificar si ya existe una corporación con el mismo nombre
    nombre = corporation_data.nombre
    descripcion = corporation_data.descripcion

    stmt = select(GrupoCorporativo).where(GrupoCorporativo.nombre == nombre)
    result = await db.execute(stmt)
    existing_corp = result.scalar_one_or_none()
    
    if existing_corp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una corporación con ese nombre"
        )
    
    # Crear la nueva corporación
    nueva_corporacion = GrupoCorporativo(
        nombre=nombre,
        descripcion=descripcion,
        is_active=True
    )
    
    db.add(nueva_corporacion)
    await db.commit()
    await db.refresh(nueva_corporacion)
    
    return {
        "mensaje": "Corporación creada exitosamente",
        "corporation_id": nueva_corporacion.id
    }

@router.put("/corporaciones/{corporation_id}")
async def actualizar_corporacion(
    corporation_id: str,
    corporation_data: GrupoCorporativoUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza datos de una corporacion sin borrar su historial ni sus tenants.
    """
    stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == corporation_id)
    result = await db.execute(stmt)
    corporation = result.scalar_one_or_none()

    if not corporation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporacion no encontrada"
        )

    data = corporation_data.model_dump(exclude_unset=True)

    if data.get("nombre") and data["nombre"] != corporation.nombre:
        stmt = select(GrupoCorporativo).where(
            GrupoCorporativo.nombre == data["nombre"],
            cast(GrupoCorporativo.id, String) != corporation_id
        )
        result = await db.execute(stmt)
        existing_corp = result.scalar_one_or_none()

        if existing_corp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una corporacion con ese nombre"
            )

    for field, value in data.items():
        setattr(corporation, field, value)

    await db.commit()
    await db.refresh(corporation)

    return {
        "mensaje": "Corporacion actualizada exitosamente",
        "corporation_id": corporation.id
    }


@router.put("/corporaciones/{corporation_id}/desactivar")
async def desactivar_corporacion(
    corporation_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == corporation_id)
    result = await db.execute(stmt)
    corporation = result.scalar_one_or_none()

    if not corporation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporacion no encontrada"
        )

    corporation.is_active = False
    await db.commit()

    return {"mensaje": f"Corporacion {corporation.nombre} desactivada exitosamente"}


@router.put("/corporaciones/{corporation_id}/activar")
async def activar_corporacion(
    corporation_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == corporation_id)
    result = await db.execute(stmt)
    corporation = result.scalar_one_or_none()

    if not corporation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporacion no encontrada"
        )

    corporation.is_active = True
    await db.commit()

    return {"mensaje": f"Corporacion {corporation.nombre} activada exitosamente"}


@router.post("/asignar-tenant-a-corporacion")
async def asignar_tenant_a_corporacion(
    assign_data: AssignTenantCorporationRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para asignar un tenant a una corporación
    """
    tenant_id = assign_data.tenant_id
    corporation_id = assign_data.corporation_id

    # Verificar que el tenant existe
    stmt = select(Tenant).where(cast(Tenant.id, String) == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Verificar que la corporación existe
    stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == corporation_id)
    result = await db.execute(stmt)
    corporation = result.scalar_one_or_none()
    
    if not corporation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporación no encontrada"
        )
    
    # Actualizar el tenant con la corporación
    stmt = update(Tenant).where(cast(Tenant.id, String) == tenant_id).values(grupo_corporativo_id=corporation_id)
    await db.execute(stmt)
    await db.commit()
    
    return {
        "mensaje": "Tenant asignado a corporación exitosamente"
    }


@router.put("/corporaciones/{corporation_id}/tenants")
async def asignar_tenants_a_corporacion(
    corporation_id: str,
    assign_data: AssignCorporationTenantsRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Reemplaza la lista de empresas asociadas a una corporacion.
    Permite que una corporacion tenga multiples tenants/empresas.
    """
    stmt = select(GrupoCorporativo).where(cast(GrupoCorporativo.id, String) == corporation_id)
    result = await db.execute(stmt)
    corporation = result.scalar_one_or_none()

    if not corporation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporacion no encontrada"
        )

    tenant_ids = list(dict.fromkeys(assign_data.tenant_ids))

    if tenant_ids:
        stmt = select(Tenant).where(cast(Tenant.id, String).in_(tenant_ids))
        result = await db.execute(stmt)
        found_tenants = result.scalars().all()
        found_ids = {str(tenant.id) for tenant in found_tenants}
        missing_ids = [tenant_id for tenant_id in tenant_ids if tenant_id not in found_ids]

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenants no encontrados: {', '.join(missing_ids)}"
            )

    await db.execute(
        update(Tenant)
        .where(cast(Tenant.grupo_corporativo_id, String) == corporation_id)
        .values(grupo_corporativo_id=None)
    )

    if tenant_ids:
        await db.execute(
            update(Tenant)
            .where(cast(Tenant.id, String).in_(tenant_ids))
            .values(grupo_corporativo_id=corporation_id)
        )

    await db.commit()

    return {
        "mensaje": "Empresas asignadas a corporacion exitosamente",
        "corporation_id": corporation_id,
        "tenant_ids": tenant_ids
    }

@router.post("/crear-licencia")
async def crear_licencia(
    licencia_data: LicenciaCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear una nueva licencia
    """
    # Verificar que el tipo de licencia existe
    stmt = select(TipoLicencia).where(TipoLicencia.id == licencia_data.tipo_licencia_id)
    result = await db.execute(stmt)
    tipo_licencia = result.scalar_one_or_none()
    
    if not tipo_licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de licencia no encontrado"
        )
    
    # Si se especifica tenant_id, verificar que existe
    if licencia_data.tenant_id:
        stmt = select(Tenant).where(cast(Tenant.id, String) == licencia_data.tenant_id)
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )
    
    # Generar código único para la licencia
    codigo_licencia = generar_token_unico(16)
    
    # Crear la nueva licencia
    nueva_licencia = Licencia(
        tipo_licencia_id=licencia_data.tipo_licencia_id,
        codigo=codigo_licencia,  # Usar el código generado
        fecha_inicio=licencia_data.fecha_inicio or datetime.utcnow(),
        fecha_fin=licencia_data.fecha_fin,
        activa=licencia_data.activa,
        tenant_id=licencia_data.tenant_id
    )
    
    db.add(nueva_licencia)
    await db.commit()
    await db.refresh(nueva_licencia)
    
    return {
        "mensaje": "Licencia creada exitosamente",
        "licencia_id": nueva_licencia.id,
        "codigo": codigo_licencia
    }

@router.get("/tenants")
async def listar_tenants(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para listar todos los tenants (solo para superadmin)
    """
    stmt = select(Tenant).offset(skip).limit(limit)
    result = await db.execute(stmt)
    tenants = result.scalars().all()

    return {
        "tenants": [
            {
                "id": tenant.id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "schema_name": tenant.schema_name,
                "contact_email": tenant.contact_email,
                "contact_phone": tenant.contact_phone,
                "descripcion": tenant.descripcion,
                "is_active": tenant.is_active,
                "es_grupo_corporativo": tenant.es_grupo_corporativo,
                "grupo_corporativo_id": tenant.grupo_corporativo_id,
                "created_at": tenant.created_at,
            }
            for tenant in tenants
        ]
    }

@router.get("/corporaciones")
async def listar_corporaciones(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para listar todas las corporaciones (solo para superadmin)
    """
    stmt = select(GrupoCorporativo).offset(skip).limit(limit)
    result = await db.execute(stmt)
    corporaciones = result.scalars().all()

    tenants_result = await db.execute(select(Tenant))
    tenants = tenants_result.scalars().all()
    
    return {
        "corporaciones": [
            {
                "id": corporacion.id,
                "name": corporacion.nombre,
                "descripcion": corporacion.descripcion,
                "is_active": corporacion.is_active,
                "empresas_count": len([tenant for tenant in tenants if tenant.grupo_corporativo_id == corporacion.id]),
                "created_at": corporacion.created_at,
            }
            for corporacion in corporaciones
        ]
    }

@router.get("/licencias")
async def listar_licencias(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para listar todas las licencias (solo para superadmin)
    """
    stmt = select(Licencia).offset(skip).limit(limit)
    result = await db.execute(stmt)
    licencias = result.scalars().all()
    
    return {"licencias": licencias}

@router.get("/licencias-por-tenant/{tenant_id}")
async def listar_licencias_por_tenant(
    tenant_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para listar licencias asociadas a un tenant específico
    """
    stmt = select(Licencia).where(cast(Licencia.tenant_id, String) == tenant_id)
    result = await db.execute(stmt)
    licencias = result.scalars().all()
    
    return {"licencias": licencias}

@router.put("/desactivar-tenant/{tenant_id}")
async def desactivar_tenant(
    tenant_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para desactivar un tenant (no eliminarlo completamente)
    """
    stmt = select(Tenant).where(cast(Tenant.id, String) == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Actualizar el estado del tenant
    stmt = update(Tenant).where(cast(Tenant.id, String) == tenant_id).values(is_active=False)
    await db.execute(stmt)
    await db.commit()
    
    return {"mensaje": f"Tenant {tenant.name} desactivado exitosamente"}

@router.put("/activar-tenant/{tenant_id}")
async def activar_tenant(
    tenant_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para reactivar un tenant
    """
    stmt = select(Tenant).where(cast(Tenant.id, String) == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Actualizar el estado del tenant
    stmt = update(Tenant).where(cast(Tenant.id, String) == tenant_id).values(is_active=True)
    await db.execute(stmt)
    await db.commit()
    
    return {"mensaje": f"Tenant {tenant.name} activado exitosamente"}
