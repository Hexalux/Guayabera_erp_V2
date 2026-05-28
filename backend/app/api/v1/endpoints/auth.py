from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import jwt
import secrets
import string
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.admin import Admin
from app.models.token import TokenVerificacion
from app.models.licencia import Licencia, TipoLicencia
from app.schemas.token import (
    SolicitudRegistro, 
    SolicitudRecuperacion, 
    ConfirmacionToken, 
    TokenVerificacionCreate,
    TokenVerificacionOut
)
from app.schemas.usuario import UsuarioCreate
from app.core.security import get_password_hash, verify_password

router = APIRouter()

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de seguridad
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: Optional[str] = None  # Opcional para superusuarios


def build_auth_payload(user):
    user_type = "admin" if isinstance(user, Admin) else "user"
    tipo_usuario = "superuser" if isinstance(user, Admin) else getattr(user, "tipo_usuario", "normal")
    user_id = str(user.id)
    token_data = {
        "sub": user_id,
        "email": user.email,
        "user_type": user_type,
        "tipo_usuario": tipo_usuario,
    }
    public_user = {
        "id": user_id,
        "email": user.email,
        "nombre_completo": getattr(user, "nombre_completo", None),
        "user_type": user_type,
        "tipo_usuario": tipo_usuario,
    }
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id:
        token_data["tenant_id"] = str(tenant_id)
        public_user["tenant_id"] = str(tenant_id)
    return token_data, public_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def authenticate_user(db: AsyncSession, email: str, password: str, tenant_id: Optional[str] = None):
    # Primero intentar encontrar un usuario normal
    stmt = select(Usuario).where(Usuario.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        # Si el usuario pertenece a un tenant, verificar que coincida
        if tenant_id and user.tenant_id != tenant_id:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    # Si no se encontró usuario normal, buscar en admins
    stmt = select(Admin).where(Admin.email == email)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()
    
    if admin and admin.is_active and verify_password(password, admin.hashed_password):
        return admin
    
    return None


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint para autenticación de usuarios.
    Si es un superusuario, no requiere tenant_id.
    Si es un usuario normal, requiere tenant_id.
    """
    user_exists_result = await db.execute(select(Usuario.id).where(Usuario.email == request.email))
    admin_exists_result = await db.execute(select(Admin.id).where(Admin.email == request.email))

    if not user_exists_result.scalar_one_or_none() and not admin_exists_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "EMAIL_NOT_FOUND",
                "message": "Correo no registrado",
            },
        )

    user = await authenticate_user(
        db, 
        request.email, 
        request.password, 
        request.tenant_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el usuario tiene licencia activa (excepto para admins)
    if isinstance(user, Usuario) and user.tenant_id:
        # Verificar licencia del tenant
        stmt = select(Licencia).where(
            Licencia.tenant_id == user.tenant_id,
            Licencia.activa == True,
            Licencia.fecha_fin > datetime.utcnow()
        )
        licencia_result = await db.execute(stmt)
        licencia_activa = licencia_result.scalar_one_or_none()
        
        if not licencia_activa:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Licencia expirada o inactiva. Por favor renueve su licencia."
            )
    
    user_data, public_user = build_auth_payload(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": public_user}


def generar_token_unico(longitud: int = 32) -> str:
    """Genera un token único seguro"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(longitud))


def enviar_correo(destinatario: str, asunto: str, cuerpo: str):
    """Función para enviar correos electrónicos (simulación)"""
    # Aquí iría la lógica real para enviar correos
    # Por ahora solo imprimimos para simular
    print(f"Correo enviado a: {destinatario}")
    print(f"Asunto: {asunto}")
    print(f"Cuerpo: {cuerpo}")


@router.post("/solicitar-registro")
async def solicitar_registro(
    solicitud: SolicitudRegistro,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para solicitar registro de nuevo usuario.
    Se envía un correo con un enlace de verificación.
    """
    # Verificar si el email ya existe
    stmt = select(Usuario).where(Usuario.email == solicitud.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Generar token de verificación
    token_verificacion = generar_token_unico()
    expiracion = datetime.utcnow() + timedelta(hours=24)  # El enlace expira en 24 horas
    
    # Crear un nuevo tenant para el usuario (simplificado)
    from app.models.tenant import Tenant
    nuevo_tenant = Tenant(
        name=solicitud.nombre_completo.split()[0] if solicitud.nombre_completo else "Nuevo Cliente",
        subdomain=solicitud.email.split('@')[0],
        schema_name=f"tenant_{solicitud.email.split('@')[0]}",
        contact_email=solicitud.email,
        descripcion="Tenant creado automáticamente durante registro"
    )
    
    db.add(nuevo_tenant)
    await db.commit()
    await db.refresh(nuevo_tenant)
    
    # Guardar el token con referencia al tenant
    nuevo_token = TokenVerificacion(
        tipo_token="registro",
        token=token_verificacion,
        expira_en=expiracion,
        usado=False,
        tenant_id=nuevo_tenant.id,
        destinatario_email=solicitud.email,
        nombre_completo=solicitud.nombre_completo
    )
    
    db.add(nuevo_token)
    await db.commit()
    await db.refresh(nuevo_token)
    
    # Enviar correo con el enlace de verificación
    enlace_verificacion = f"{settings.FRONTEND_URL}/crear-cuenta/{token_verificacion}"
    cuerpo_correo = f"""
    Hola {solicitud.nombre_completo or 'Usuario'},
    
    Gracias por registrarte en Guayabera ERP Suite.
    
    Por favor haz clic en el siguiente enlace para crear tu contraseña y activar tu cuenta:
    {enlace_verificacion}
    
    Este enlace es válido por 24 horas. Si no solicitaste este registro, puedes ignorar este mensaje.
    
    Saludos,
    Equipo de Guayabera ERP Suite
    """
    
    # Enviar correo
    enviar_correo(solicitud.email, "Verificación de Registro - Guayabera ERP Suite", cuerpo_correo)
    
    return {
        "mensaje": "Se ha enviado un enlace de verificación a su correo electrónico. "
                   "Por favor revise su bandeja de entrada (y la carpeta de correo no deseado si es necesario).",
        "token_info": {
            "expira_en": expiracion.isoformat()
        }
    }


@router.post("/confirmar-registro/{token}")
async def confirmar_registro(
    token: str,
    request: ConfirmacionToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para confirmar el registro y crear la cuenta con contraseña
    """
    # Buscar el token de verificación
    stmt = select(TokenVerificacion).where(
        TokenVerificacion.token == token,
        TokenVerificacion.tipo_token.in_(["registro", "invitacion_tenant_admin"]),
        TokenVerificacion.usado == False,
        TokenVerificacion.expira_en > datetime.utcnow()
    )
    result = await db.execute(stmt)
    token_verif = result.scalar_one_or_none()
    
    if not token_verif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, expirado o ya utilizado"
        )
    
    if not request.nueva_contrasena:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrasena es requerida"
        )

    if not token_verif.destinatario_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sin correo asociado"
        )

    stmt = select(Usuario).where(Usuario.email == token_verif.destinatario_email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya esta registrado"
        )
    
    hashed_password = get_password_hash(request.nueva_contrasena)
    nuevo_usuario = Usuario(
        email=token_verif.destinatario_email,
        hashed_password=hashed_password,
        nombre_completo=token_verif.nombre_completo or token_verif.destinatario_email,
        tipo_usuario="admin_empresa" if token_verif.tipo_token in ["registro", "invitacion_tenant_admin"] else "normal",
        tenant_id=token_verif.tenant_id
    )
    
    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)
    
    # Asignar licencia de prueba de 90 días
    tipo_licencia_prueba = await db.execute(
        select(TipoLicencia).where(TipoLicencia.es_prueba == True)
    )
    tipo_licencia = tipo_licencia_prueba.scalar_one_or_none()
    
    if tipo_licencia:
        fecha_fin = datetime.utcnow() + timedelta(days=90)
        if nuevo_usuario.tenant_id:
            nueva_licencia = Licencia(
                tenant_id=nuevo_usuario.tenant_id,
                tipo_licencia_id=tipo_licencia.id,
                codigo=generar_token_unico(16),
                fecha_fin=fecha_fin,
                activa=True,
                usada=False
            )
            db.add(nueva_licencia)

    token_verif.usado = True
    await db.commit()
    
    return {"mensaje": "Cuenta creada exitosamente. Ya puede iniciar sesión."}


@router.post("/solicitar-recuperacion")
async def solicitar_recuperacion(
    solicitud: SolicitudRecuperacion,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para solicitar recuperación de contraseña.
    Se envía un correo con un enlace de recuperación.
    """
    # Buscar al usuario por email
    stmt = select(Usuario).where(Usuario.email == solicitud.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # También buscar en admins
    if not user:
        stmt = select(Admin).where(Admin.email == solicitud.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    
    if not user:
        # Para evitar revelar si un email existe o no, devolvemos el mismo mensaje
        return {
            "mensaje": "Si el email está registrado, se ha enviado un enlace de recuperación. "
                      "Por favor revise su bandeja de entrada (y la carpeta de correo no deseado si es necesario)."
        }
    
    # Generar token de recuperación
    token_recuperacion = generar_token_unico()
    expiracion = datetime.utcnow() + timedelta(hours=2)  # El enlace expira en 2 horas
    
    # Guardar el token
    nuevo_token = TokenVerificacion(
        tipo_token="recuperacion",
        token=token_recuperacion,
        expira_en=expiracion,
        usado=False
    )
    
    # Asociar al usuario correspondiente
    if isinstance(user, Usuario):
        nuevo_token.usuario_id = user.id
    elif isinstance(user, Admin):
        nuevo_token.admin_id = user.id
    
    db.add(nuevo_token)
    await db.commit()
    await db.refresh(nuevo_token)
    
    # Enviar correo con el enlace de recuperación
    enlace_recuperacion = f"{settings.FRONTEND_URL}/recuperar-contrasena/{token_recuperacion}"
    cuerpo_correo = f"""
    Estimado(a) {user.nombre_completo or 'Usuario'},
    
    Ha solicitado la recuperación de su contraseña para Guayabera ERP Suite.
    
    Por favor haga clic en el siguiente enlace para crear una nueva contraseña:
    {enlace_recuperacion}
    
    Este enlace es válido únicamente por 2 horas y solo puede ser utilizado una vez. 
    Si no solicitó este cambio, puede ignorar este mensaje.
    
    IMPORTANTE: Revise también la carpeta de correo no deseado o spam si no encuentra el mensaje en su bandeja de entrada.
    
    Saludos,
    Equipo de Seguridad de Guayabera ERP Suite
    """
    
    # Enviar correo
    enviar_correo(solicitud.email, "Recuperación de Contraseña - Guayabera ERP Suite", cuerpo_correo)
    
    return {
        "mensaje": "Si el email está registrado, se ha enviado un enlace de recuperación. "
                  "Por favor revise su bandeja de entrada (y la carpeta de correo no deseado si es necesario)."
    }


@router.post("/confirmar-recuperacion/{token}")
async def confirmar_recuperacion(
    token: str,
    request: ConfirmacionToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para confirmar la recuperación de contraseña
    """
    # Buscar el token de verificación
    stmt = select(TokenVerificacion).where(
        TokenVerificacion.token == token,
        TokenVerificacion.tipo_token == "recuperacion",
        TokenVerificacion.usado == False,
        TokenVerificacion.expira_en > datetime.utcnow()
    )
    result = await db.execute(stmt)
    token_verif = result.scalar_one_or_none()
    
    if not token_verif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, expirado o ya utilizado"
        )
    
    # Obtener el usuario correspondiente
    if token_verif.usuario_id:
        stmt = select(Usuario).where(Usuario.id == token_verif.usuario_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
    elif token_verif.admin_id:
        stmt = select(Admin).where(Admin.id == token_verif.admin_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador no encontrado"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar contraseña
    hashed_password = get_password_hash(request.nueva_contrasena)
    user.hashed_password = hashed_password
    
    # Actualizar el token como usado
    token_verif.usado = True
    await db.commit()
    
    return {"mensaje": "Contraseña actualizada exitosamente. Ya puede iniciar sesión con su nueva contraseña."}


@router.post("/register-superuser", response_model=Token)
async def register_super_user(
    request: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear el primer superusuario del sistema
    """
    # Verificar que aún no exista un superusuario
    result = await db.execute(select(Admin))
    existing_admins = result.scalars().all()
    
    if len(existing_admins) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un superusuario registrado"
        )
    
    # Crear el hash de la contraseña
    hashed_password = get_password_hash(request.password)
    
    # Crear el nuevo superusuario
    admin = Admin(
        email=request.email,
        hashed_password=hashed_password,
        nombre_completo="Super Administrador",
        is_verified=True
    )
    
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    # Crear token de autenticación
    user_data, public_user = build_auth_payload(admin)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": public_user}
