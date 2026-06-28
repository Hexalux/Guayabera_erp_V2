"""
Servicio de Terceros Unificados
Gestión de Clientes, Proveedores, Empleados y Otros
Fusión de CONTPAQi (robustez fiscal), Odoo (flexibilidad), Management Pro (opciones)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, and_, or_
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.terceros import Tercero, TerceroDireccion as DireccionTercero, TerceroContacto as ContactoTercero
from app.schemas.terceros import (
    TerceroCreate, TerceroUpdate, TerceroFiltro,
    TipoTercero, TipoDocumento
)


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class DuplicateError(Exception):
    pass


class TerceroService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generar_codigo_tercero(self, tipo: TipoTercero, tenant_id: UUID) -> str:
        """Genera código único estilo CONTPAQi (CLI-00001, PRO-00001, etc.)"""
        prefijos = {
            TipoTercero.CLIENTE: "CLI",
            TipoTercero.PROVEEDOR: "PRO",
            TipoTercero.EMPLEADO: "EMP",
            TipoTercero.ACCIONISTA: "ACC",
            TipoTercero.OTRO: "OTR"
        }
        prefijo = prefijos.get(tipo, "TER")
        
        # Obtener último consecutivo
        result = await self.db.execute(
            select(Tercero.codigo)
            .where(Tercero.tenant_id == tenant_id)
            .where(Tercero.codigo.like(f"{prefijo}-%"))
            .order_by(Tercero.codigo.desc())
            .limit(1)
        )
        ultimo = result.scalar_one_or_none()
        
        if ultimo:
            try:
                numero = int(ultimo.split("-")[1]) + 1
            except:
                numero = 1
        else:
            numero = 1
        
        return f"{prefijo}-{numero:05d}"

    async def crear_tercero(
        self, 
        data: TerceroCreate, 
        tenant_id: UUID, 
        usuario_id: UUID
    ) -> Tercero:
        # Validar que no exista identificación duplicada
        existe = await self.db.execute(
            select(Tercero.id)
            .where(Tercero.tenant_id == tenant_id)
            .where(Tercero.identificacion == data.identificacion)
            .where(Tercero.activo == True)
        )
        if existe.scalar_one_or_none():
            raise DuplicateError(
                f"Ya existe un tercero activo con identificación {data.identificacion}"
            )
        
        # Generar código automático
        codigo = await self._generar_codigo_tercero(data.tipo_tercero, tenant_id)
        
        # Crear tercero principal
        tercero_data = data.dict(exclude={'contactos', 'direcciones'})
        tercero = Tercero(
            **tercero_data,
            id=None,  # SQLAlchemy generará el UUID
            tenant_id=tenant_id,
            codigo=codigo,
            usuario_creacion=usuario_id,
            usuario_modificacion=usuario_id
        )
        
        self.db.add(tercero)
        await self.db.flush()  # Para obtener el ID generado
        
        # Crear direcciones si existen
        if data.direcciones:
            for idx, dir_data in enumerate(data.direcciones):
                direccion = DireccionTercero(
                    tercero_id=tercero.id,
                    **dir_data.dict(),
                    es_principal=(idx == 0)
                )
                self.db.add(direccion)
        
        # Crear contactos si existen
        if data.contactos:
            for idx, cont_data in enumerate(data.contactos):
                contacto = ContactoTercero(
                    tercero_id=tercero.id,
                    **cont_data.dict(),
                    es_principal=(idx == 0)
                )
                self.db.add(contacto)
        
        await self.db.commit()
        await self.db.refresh(tercero)
        return tercero

    async def obtener_tercero(self, tercero_id: UUID, tenant_id: UUID) -> Tercero:
        result = await self.db.execute(
            select(Tercero)
            .where(Tercero.id == tercero_id)
            .where(Tercero.tenant_id == tenant_id)
        )
        tercero = result.scalar_one_or_none()
        if not tercero:
            raise NotFoundError("Tercero no encontrado")
        return tercero

    async def listar_terceros(
        self, 
        filtro: TerceroFiltro, 
        tenant_id: UUID,
        limite: int = 50,
        offset: int = 0
    ) -> List[Tercero]:
        query = select(Tercero).where(Tercero.tenant_id == tenant_id)
        
        if filtro.tipo_tercero:
            query = query.where(Tercero.tipo_tercero == filtro.tipo_tercero)
        
        if filtro.identificacion:
            query = query.where(Tercero.identificacion.ilike(f"%{filtro.identificacion}%"))
        
        if filtro.razon_social:
            query = query.where(Tercero.razon_social.ilike(f"%{filtro.razon_social}%"))
        
        if filtro.activo is not None:
            query = query.where(Tercero.activo == filtro.activo)
        
        query = query.offset(offset).limit(limite).order_by(Tercero.razon_social)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def actualizar_tercero(
        self, 
        tercero_id: UUID, 
        data: TerceroUpdate, 
        tenant_id: UUID,
        usuario_id: UUID
    ) -> Tercero:
        tercero = await self.obtener_tercero(tercero_id, tenant_id)
        
        update_data = data.dict(exclude_unset=True)
        if update_data:
            update_data['usuario_modificacion'] = usuario_id
            update_data['fecha_modificacion'] = datetime.now()
            
            stmt = update(Tercero).where(Tercero.id == tercero_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(tercero)
        
        return tercero

    async def eliminar_tercero(
        self, 
        tercero_id: UUID, 
        tenant_id: UUID,
        usuario_id: UUID
    ) -> bool:
        """Eliminación lógica (soft delete)"""
        tercero = await self.obtener_tercero(tercero_id, tenant_id)
        
        # Verificar que no tenga documentos asociados con saldo
        # (En producción se verificaría CXC, CXP, facturas, etc.)
        if tercero.saldo_pendiente != 0:
            raise ValidationError(
                "No se puede eliminar un tercero con saldo pendiente"
            )
        
        stmt = update(Tercero).where(Tercero.id == tercero_id).values(
            activo=False,
            usuario_modificacion=usuario_id,
            fecha_modificacion=datetime.now()
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def obtener_resumen_cartera(
        self, 
        tercero_id: UUID, 
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Obtiene resumen de saldos para reportes"""
        tercero = await self.obtener_tercero(tercero_id, tenant_id)
        
        # En producción esto consultaría las tablas de CXC/CXP
        return {
            "tercero_id": str(tercero.id),
            "codigo": tercero.codigo,
            "razon_social": tercero.razon_social,
            "identificacion": tercero.identificacion,
            "tipo_tercero": tercero.tipo_tercero.value,
            "limite_credito": float(tercero.limite_credito) if tercero.limite_credito else None,
            "saldo_pendiente": float(tercero.saldo_pendiente),
            "saldo_vencido": float(tercero.saldo_vencido),
            "disponible_credito": (
                float(tercero.limite_credito - tercero.saldo_pendiente)
                if tercero.limite_credito else None
            ),
            "dias_plazo": tercero.dias_plazo,
            "activo": tercero.activo
        }

    async def buscar_por_identificacion(
        self, 
        identificacion: str, 
        tenant_id: UUID
    ) -> Optional[Tercero]:
        result = await self.db.execute(
            select(Tercero)
            .where(Tercero.tenant_id == tenant_id)
            .where(Tercero.identificacion == identificacion)
            .where(Tercero.activo == True)
        )
        return result.scalar_one_or_none()
