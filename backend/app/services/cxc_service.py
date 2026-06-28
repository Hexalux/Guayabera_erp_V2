"""
Servicio de Cuentas por Cobrar (CXC)
Fusión de CONTPAQi (robustez), Odoo (flexibilidad), Management Pro (opciones)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from app.models.cxc import (
    CXCDocumento, CXCMovimiento, CXCAplicacion, CXCCobro,
    RelacionCobranza, InteresMoratorio, AnticipoCliente,
    TipoDocumentoCXC, EstadoDocumentoCXC
)
from app.models.terceros import Tercero
from app.schemas.cxc import (
    DocumentoCXCCreate, DocumentoXCUpdate, CXCFiltro,
    CobroCreate, AplicacionCXCCreate, NotaCreditoCreate,
    AnticipoCreate, InteresMoratorioCalculation
)
from app.core.exceptions import NotFoundError, ValidationError, DuplicateError


class CXCService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generar_consecutivo(self, serie: str, tenant_id: UUID) -> int:
        """Genera consecutivo automático estilo CONTPAQi"""
        result = await self.db.execute(
            select(func.max(CXCDocumento.consecutivo))
            .where(CXCDocumento.tenant_id == tenant_id)
            .where(CXCDocumento.serie == serie)
        )
        ultimo = result.scalar_one_or_none()
        return (ultimo or 0) + 1

    async def crear_documento(
        self,
        data: DocumentoCXCCreate,
        tenant_id: UUID,
        usuario_id: UUID,
        serie: str = "FAC-001"
    ) -> CXCDocumento:
        """Crear documento CXC (factura, nota crédito, etc.)"""
        
        # Validar cliente
        cliente = await self.db.get(Tercero, data.cliente_id)
        if not cliente:
            raise NotFoundError("Cliente no encontrado")
        
        # Generar consecutivo
        consecutivo = await self._generar_consecutivo(serie, tenant_id)
        folio = f"{serie}-{consecutivo:08d}"
        
        # Calcular fecha de vencimiento si no se proporcionó
        fecha_vencimiento = data.fecha_vencimiento
        if not fecha_vencimiento and data.dias_plazo > 0:
            fecha_vencimiento = data.fecha_emision + timedelta(days=data.dias_plazo)
        
        documento = CXCDocumento(
            tenant_id=tenant_id,
            codigo=f"CXC-{datetime.now().strftime('%Y%m')}-{consecutivo:06d}",
            tipo_documento=data.tipo_documento,
            serie=serie,
            consecutivo=consecutivo,
            folio=folio,
            cliente_id=data.cliente_id,
            fecha_emision=data.fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            forma_pago=data.forma_pago,
            dias_plazo=data.dias_plazo,
            subtotal=float(data.subtotal),
            descuento=float(data.descuento),
            iva=float(data.iva),
            ice=float(data.ice),
            otros_impuestos=float(data.otros_impuestos),
            total=float(data.total),
            saldo_pendiente=float(data.total),
            moneda=data.moneda,
            tipo_cambio=float(data.tipo_cambio),
            cuenta_contable=data.cuenta_contable,
            centro_costo_id=data.centro_costo_id,
            vendedor_id=data.vendedor_id,
            comision_porcentaje=float(data.comision_porcentaje),
            estado=EstadoDocumentoCXC.REGISTRADO,
            usuario_creacion=usuario_id,
            observaciones=data.observaciones
        )
        
        self.db.add(documento)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(documento)
        
        # Registrar movimiento inicial
        await self._registrar_movimiento(
            documento_id=documento.id,
            tipo_movimiento="Emisión",
            valor_original=float(data.total),
            saldo_nuevo=float(data.total),
            usuario_id=usuario_id,
            tenant_id=tenant_id
        )
        
        return documento

    async def _registrar_movimiento(
        self,
        documento_id: UUID,
        tipo_movimiento: str,
        valor_original: float,
        saldo_nuevo: float,
        usuario_id: UUID,
        tenant_id: UUID,
        documento_relacionado_id: Optional[UUID] = None,
        observaciones: Optional[str] = None
    ):
        """Registrar movimiento en el historial del documento"""
        movimiento = CXCMovimiento(
            tenant_id=tenant_id,
            documento_id=documento_id,
            tipo_movimiento=tipo_movimiento,
            valor_original=valor_original,
            valor_aplicado=0,
            saldo_anterior=0,  # Se calculará en producción
            saldo_nuevo=saldo_nuevo,
            documento_relacionado_id=documento_relacionado_id,
            usuario_creacion=usuario_id,
            observaciones=observaciones
        )
        self.db.add(movimiento)
        await self.db.flush()

    async def registrar_cobro(
        self,
        data: CobroCreate,
        tenant_id: UUID,
        usuario_id: UUID
    ) -> CXCCobro:
        """Registrar cobro y aplicar a documentos"""
        
        # Crear cobro
        cobro = CXCCobro(
            tenant_id=tenant_id,
            codigo=f"COB-{datetime.now().strftime('%Y%m%d')}-{func.nextval('cobro_seq')}",
            cliente_id=data.cliente_id,
            fecha_cobro=data.fecha_cobro,
            forma_pago=data.forma_pago,
            referencia_pago=data.referencia_pago,
            banco_id=data.banco_id,
            numero_cheque=data.numero_cheque,
            subtotal=float(data.subtotal),
            descuento=float(data.descuento),
            iva=float(data.iva),
            total=float(data.total),
            saldo_pendiente=float(data.total),
            estado="pendiente",
            usuario_creacion=usuario_id,
            observaciones=data.observaciones
        )
        
        self.db.add(cobro)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(cobro)
        
        # Aplicar a documentos si se especificaron
        if data.documentos_a_aplicar:
            for aplicacion in data.documentos_a_aplicar:
                await self.aplicar_pago_documento(
                    documento_pago_id=cobro.id,
                    documento_aplicado_id=UUID(aplicacion['documento_id']),
                    valor_aplicado=Decimal(str(aplicacion['valor'])),
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    tipo_aplicacion="pago"
                )
        
        return cobro

    async def aplicar_pago_documento(
        self,
        documento_pago_id: UUID,
        documento_aplicado_id: UUID,
        valor_aplicado: Decimal,
        tenant_id: UUID,
        usuario_id: UUID,
        tipo_aplicacion: str = "pago",
        observaciones: Optional[str] = None
    ) -> CXCAplicacion:
        """Aplicar pago o nota de crédito a un documento"""
        
        # Obtener documento a aplicar
        documento = await self.db.get(CXCDocumento, documento_aplicado_id)
        if not documento:
            raise NotFoundError("Documento no encontrado")
        
        # Validar que tenga saldo pendiente
        if Decimal(str(documento.saldo_pendiente)) <= 0:
            raise ValidationError("El documento no tiene saldo pendiente")
        
        # Validar que el valor no exceda el saldo
        if valor_aplicado > Decimal(str(documento.saldo_pendiente)):
            raise ValidationError(
                f"El valor aplicado ({valor_aplicado}) excede el saldo pendiente ({documento.saldo_pendiente})"
            )
        
        # Crear aplicación
        aplicacion = CXCAplicacion(
            tenant_id=tenant_id,
            documento_pago_id=documento_pago_id,
            documento_aplicado_id=documento_aplicado_id,
            valor_aplicado=float(valor_aplicado),
            tipo_aplicacion=tipo_aplicacion,
            usuario_creacion=usuario_id,
            observaciones=observaciones
        )
        
        self.db.add(aplicacion)
        
        # Actualizar saldo del documento
        nuevo_saldo = float(Decimal(str(documento.saldo_pendiente)) - valor_aplicado)
        documento.saldo_pendiente = nuevo_saldo
        
        # Actualizar estado
        if nuevo_saldo <= 0:
            documento.estado = EstadoDocumentoCXC.SALDADO
            documento.es_aplicado = True
        elif nuevo_saldo < float(documento.total):
            documento.estado = EstadoDocumentoCXC.PARCIAL
        
        await self.db.commit()
        await self.db.refresh(aplicacion)
        
        # Registrar movimiento
        await self._registrar_movimiento(
            documento_id=documento_aplicado_id,
            tipo_movimiento=f"Aplicación {tipo_aplicacion}",
            valor_original=float(valor_aplicado),
            saldo_nuevo=nuevo_saldo,
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            documento_relacionado_id=documento_pago_id,
            observaciones=observaciones
        )
        
        return aplicacion

    async def crear_nota_credito(
        self,
        data: NotaCreditoCreate,
        tenant_id: UUID,
        usuario_id: UUID,
        serie: str = "NCR-001"
    ) -> CXCDocumento:
        """Crear nota de crédito"""
        
        # Validar documento origen si existe
        if data.documento_origen_id:
            documento_origen = await self.db.get(CXCDocumento, data.documento_origen_id)
            if not documento_origen:
                raise NotFoundError("Documento origen no encontrado")
        
        # Crear como documento normal con tipo NOTA_CREDITO
        doc_data = DocumentoCXCCreate(
            tipo_documento=TipoDocumentoCXC.NOTA_CREDITO,
            cliente_id=data.cliente_id,
            fecha_emision=data.fecha_emision,
            fecha_vencimiento=data.fecha_vencimiento,
            subtotal=data.subtotal,
            descuento=data.descuento,
            iva=data.iva,
            ice=data.ice,
            otros_impuestos=data.otros_impuestos,
            total=data.total,
            forma_pago=data.forma_pago,
            observaciones=f"Nota de crédito: {data.motivo}"
        )
        
        documento = await self.crear_documento(
            data=doc_data,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            serie=serie
        )
        
        # Vincular con documento origen
        documento.documento_origen_id = data.documento_origen_id
        documento.documento_relacionado = data.motivo[:100] if data.motivo else None
        await self.db.commit()
        
        return documento

    async def calcular_intereses_moratorios(
        self,
        data: InteresMoratorioCalculation,
        tenant_id: UUID,
        usuario_id: UUID
    ) -> Dict[str, Any]:
        """Calcular intereses moratorios para un documento"""
        
        documento = await self.db.get(CXCDocumento, data.documento_id)
        if not documento:
            raise NotFoundError("Documento no encontrado")
        
        # Calcular días de mora
        hoy = data.fecha_calculo
        dias_mora = (hoy - documento.fecha_vencimiento).days
        
        # Restar días de gracia
        dias_mora_reales = max(0, dias_mora - data.dias_gracia)
        
        if dias_mora_reales <= 0:
            return {
                "documento_id": str(documento.id),
                "dias_mora": 0,
                "valor_interes": Decimal('0'),
                "mensaje": "El documento no está en mora"
            }
        
        # Calcular interés: (saldo * tasa * días) / 360
        base_calculo = Decimal(str(documento.saldo_vencido or documento.saldo_pendiente))
        valor_interes = (base_calculo * data.tasa_interes_anual * Decimal(str(dias_mora_reales))) / Decimal('360')
        
        return {
            "documento_id": str(documento.id),
            "documento_codigo": documento.codigo,
            "fecha_vencimiento": documento.fecha_vencimiento,
            "dias_mora": dias_mora_reales,
            "tasa_interes_anual": data.tasa_interes_anual,
            "base_calculo": base_calculo,
            "valor_interes": valor_interes.quantize(Decimal('0.01'))
        }

    async def obtener_resumen_cartera(
        self,
        cliente_id: UUID,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Obtener resumen de cartera de un cliente"""
        
        cliente = await self.db.get(Tercero, cliente_id)
        if not cliente:
            raise NotFoundError("Cliente no encontrado")
        
        # Consultar documentos pendientes
        result = await self.db.execute(
            select(
                func.sum(CXCDocumento.saldo_pendiente),
                func.sum(CXCDocumento.saldo_vencido),
                func.count(CXCDocumento.id)
            )
            .where(CXCDocumento.tenant_id == tenant_id)
            .where(CXCDocumento.cliente_id == cliente_id)
            .where(CXCDocumento.estado.in_([EstadoDocumentoCXC.PENDIENTE, EstadoDocumentoCXC.PARCIAL]))
        )
        
        row = result.one()
        saldo_total = float(row[0] or 0)
        saldo_vencido = float(row[1] or 0)
        total_documentos = row[2] or 0
        
        return {
            "cliente_id": str(cliente.id),
            "cliente_nombre": cliente.razon_social,
            "cliente_identificacion": cliente.identificacion,
            "limite_credito": cliente.limite_credito,
            "saldo_total": saldo_total,
            "saldo_vencido": saldo_vencido,
            "saldo_por_vencer": saldo_total - saldo_vencido,
            "disponible_credito": (
                float(cliente.limite_credito - saldo_total)
                if cliente.limite_credito else None
            ),
            "documentos_pendientes": total_documentos
        }

    async def listar_documentos(
        self,
        filtro: CXCFiltro,
        tenant_id: UUID,
        limite: int = 50,
        offset: int = 0
    ) -> List[CXCDocumento]:
        """Listar documentos CXC con filtros"""
        
        query = select(CXCDocumento).where(CXCDocumento.tenant_id == tenant_id)
        
        if filtro.tipo_documento:
            query = query.where(CXCDocumento.tipo_documento == filtro.tipo_documento)
        
        if filtro.cliente_id:
            query = query.where(CXCDocumento.cliente_id == filtro.cliente_id)
        
        if filtro.estado:
            query = query.where(CXCDocumento.estado == filtro.estado)
        
        if filtro.fecha_desde:
            query = query.where(CXCDocumento.fecha_emision >= filtro.fecha_desde)
        
        if filtro.fecha_hasta:
            query = query.where(CXCDocumento.fecha_emision <= filtro.fecha_hasta)
        
        if filtro.vencido is not None:
            hoy = date.today()
            if filtro.vencido:
                query = query.where(and_(
                    CXCDocumento.fecha_vencimiento < hoy,
                    CXCDocumento.saldo_pendiente > 0
                ))
            else:
                query = query.where(or_(
                    CXCDocumento.fecha_vencimiento >= hoy,
                    CXCDocumento.saldo_pendiente == 0
                ))
        
        query = query.offset(offset).limit(limite).order_by(CXCDocumento.fecha_emision.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
