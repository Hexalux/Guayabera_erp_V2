from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import date

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.hr import (
    Departamento, Empleado, ControlVacaciones, NoticiaHR, Inasistencia, RegistroAsistencia, Nomina,
    ContratoLaboral, SATCatalogoPercepcion, SATCatalogoDeduccion, TablaISR, ParametroFiscal
)

# Schemas
from app.schemas.hr import (
    DepartamentoCreate, DepartamentoResponse,
    EmpleadoCreate, EmpleadoResponse, EmpleadoUpdate,
    ControlVacacionesCreate, ControlVacacionesResponse,
    NoticiaHRCreate, NoticiaHRResponse,
    InasistenciaCreate, InasistenciaResponse,
    RegistroAsistenciaCreate, RegistroAsistenciaResponse,
    HuellaEnroll,
    NominaCreate, NominaResponse,
    ContratoLaboralCreate, ContratoLaboralResponse,
    SATCatalogoResponse,
    CalculoNominaRequest, CalculoNominaResponse,
    ParametroFiscalResponse, TablaISRResponse
)

from app.services.pac_service import pac_service

router = APIRouter()

# =================================================================
# DEPARTAMENTOS
# =================================================================
@router.get("/departamentos", response_model=List[DepartamentoResponse])
async def list_departamentos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Departamento).where(Departamento.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/departamentos", response_model=DepartamentoResponse, status_code=status.HTTP_201_CREATED)
async def create_departamento(
    dep: DepartamentoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_dep = Departamento(**dep.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_dep)
    await db.commit()
    await db.refresh(db_dep)
    return db_dep

# =================================================================
# EMPLEADOS Y ORGANIGRAMA
# =================================================================
@router.get("/empleados", response_model=List[EmpleadoResponse])
async def list_empleados(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Empleado).where(Empleado.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/empleados", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
async def create_empleado(
    emp: EmpleadoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_emp = Empleado(**emp.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_emp)
    await db.commit()
    await db.refresh(db_emp)
    return db_emp

@router.put("/empleados/{id}", response_model=EmpleadoResponse)
async def update_empleado(
    id: str,
    emp_update: EmpleadoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Empleado).where(Empleado.id == id, Empleado.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_emp = result.scalar_one_or_none()
    
    if not db_emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    update_data = emp_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_emp, key, value)
        
    await db.commit()
    await db.refresh(db_emp)
    return db_emp

# =================================================================
# NOTICIAS (TABLÓN)
# =================================================================
@router.get("/noticias", response_model=List[NoticiaHRResponse])
async def list_noticias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(NoticiaHR).where(NoticiaHR.tenant_id == current_user.tenant_id).order_by(NoticiaHR.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/noticias", response_model=NoticiaHRResponse, status_code=status.HTTP_201_CREATED)
async def create_noticia(
    noticia: NoticiaHRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_noticia = NoticiaHR(**noticia.model_dump(), autor=current_user.nombre, tenant_id=current_user.tenant_id)
    db.add(db_noticia)
    await db.commit()
    await db.refresh(db_noticia)
    return db_noticia

# =================================================================
# VACACIONES
# =================================================================
@router.get("/vacaciones", response_model=List[ControlVacacionesResponse])
async def list_vacaciones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(ControlVacaciones).where(ControlVacaciones.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/vacaciones", response_model=ControlVacacionesResponse, status_code=status.HTTP_201_CREATED)
async def request_vacaciones(
    vac: ControlVacacionesCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_vac = ControlVacaciones(**vac.model_dump(), estado="pendiente", tenant_id=current_user.tenant_id)
    db.add(db_vac)
    await db.commit()
    await db.refresh(db_vac)
    return db_vac

@router.put("/vacaciones/{id}/approve", response_model=ControlVacacionesResponse)
async def approve_vacaciones(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(ControlVacaciones).where(ControlVacaciones.id == id, ControlVacaciones.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_vac = result.scalar_one_or_none()
    
    if not db_vac:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
    db_vac.estado = "aprobada"
    await db.commit()
    await db.refresh(db_vac)
    return db_vac

@router.put("/vacaciones/{id}/reject", response_model=ControlVacacionesResponse)
async def reject_vacaciones(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(ControlVacaciones).where(ControlVacaciones.id == id, ControlVacaciones.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_vac = result.scalar_one_or_none()
    
    if not db_vac:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
    db_vac.estado = "rechazada"
    await db.commit()
    await db.refresh(db_vac)
    return db_vac

# =================================================================
# INASISTENCIAS
# =================================================================
@router.get("/inasistencias", response_model=List[InasistenciaResponse])
async def list_inasistencias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Inasistencia).where(Inasistencia.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/inasistencias", response_model=InasistenciaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_inasistencia(
    inasist: InasistenciaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_ina = Inasistencia(**inasist.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_ina)
    await db.commit()
    await db.refresh(db_ina)
    return db_ina

# =================================================================
# ASISTENCIA Y BIOMETRÍA
# =================================================================
@router.post("/asistencia/enroll", response_model=EmpleadoResponse)
async def enroll_huella(
    enroll_data: HuellaEnroll,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Empleado).where(Empleado.id == enroll_data.empleado_id, Empleado.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_emp = result.scalar_one_or_none()
    
    if not db_emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    db_emp.huella_template = enroll_data.template_base64
    await db.commit()
    await db.refresh(db_emp)
    return db_emp

@router.post("/asistencia/check", response_model=RegistroAsistenciaResponse, status_code=status.HTTP_201_CREATED)
async def check_asistencia(
    registro: RegistroAsistenciaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_reg = RegistroAsistencia(**registro.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_reg)
    await db.commit()
    await db.refresh(db_reg)
    return db_reg

@router.post("/asistencia/sync", response_model=List[RegistroAsistenciaResponse])
async def sync_asistencia(
    registros: List[RegistroAsistenciaCreate],
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    nuevos_registros = []
    for reg in registros:
        db_reg = RegistroAsistencia(**reg.model_dump(), tenant_id=current_user.tenant_id, offline_sync=True)
        db.add(db_reg)
        nuevos_registros.append(db_reg)
        
    await db.commit()
    for reg in nuevos_registros:
        await db.refresh(reg)
    return nuevos_registros

@router.get("/asistencia", response_model=List[RegistroAsistenciaResponse])
async def list_asistencias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(RegistroAsistencia).where(RegistroAsistencia.tenant_id == current_user.tenant_id).order_by(RegistroAsistencia.fecha_hora.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# =================================================================
# NÓMINA (BÁSICO)
# =================================================================
@router.get("/nominas", response_model=List[NominaResponse])
async def list_nominas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Nomina).where(Nomina.tenant_id == current_user.tenant_id).order_by(Nomina.fecha_pago.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/nominas", response_model=NominaResponse, status_code=status.HTTP_201_CREATED)
async def create_nomina(
    nomina: NominaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_nom = Nomina(**nomina.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_nom)
    await db.commit()
    await db.refresh(db_nom)
    return db_nom

@router.post("/nominas/{nomina_id}/timbrar")
async def timbrar_nomina(
    nomina_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Nomina).where(Nomina.id == nomina_id, Nomina.tenant_id == current_user.tenant_id)
    res = await db.execute(stmt)
    nomina = res.scalar_one_or_none()
    
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")
        
    if nomina.estado_timbrado == "TIMBRADO":
        raise HTTPException(status_code=400, detail="Esta nómina ya fue timbrada previamente")
        
    # Obtener empleado para RFC
    stmt_emp = select(Empleado).where(Empleado.id == nomina.empleado_id)
    res_emp = await db.execute(stmt_emp)
    empleado = res_emp.scalar_one_or_none()
    
    rfc_receptor = getattr(empleado, "rfc", "XAXX010101000") # Default para test
    
    # Llamar al PAC Mock
    pac_res = await pac_service.timbrar_nomina(
        nomina_id=nomina.id,
        empleado_rfc=rfc_receptor,
        percepciones=float(nomina.total_percepciones),
        deducciones=float(nomina.total_deducciones)
    )
    
    if not pac_res["success"]:
        nomina.estado_timbrado = "ERROR"
        await db.commit()
        raise HTTPException(status_code=400, detail=pac_res.get("error", "Error desconocido en el PAC"))
        
    data = pac_res["data"]
    nomina.uuid_cfdi = data["uuid"]
    nomina.url_xml = data["url_xml"]
    nomina.url_pdf = data["url_pdf"]
    nomina.estado_timbrado = "TIMBRADO"
    
    await db.commit()
    await db.refresh(nomina)
    
    return {"mensaje": data["mensaje"], "nomina": nomina}

@router.post("/nominas/calcular", response_model=CalculoNominaResponse)
async def calcular_nomina(
    req: CalculoNominaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Obtener Contrato Activo
    stmt_contrato = select(ContratoLaboral).where(
        ContratoLaboral.empleado_id == req.empleado_id,
        ContratoLaboral.tenant_id == current_user.tenant_id,
        ContratoLaboral.is_active == True
    )
    res_contrato = await db.execute(stmt_contrato)
    contrato = res_contrato.scalar_one_or_none()
    
    if not contrato:
        raise HTTPException(status_code=400, detail="Empleado sin contrato activo")
        
    sbc = float(contrato.salario_base_cotizacion) if contrato.salario_base_cotizacion else float(contrato.salario_diario)
    sd = float(contrato.salario_diario)
    
    ingreso_gravable = sd * req.dias_periodo
    
    # Obtener Parametros (UMA, SMI)
    stmt_params = select(ParametroFiscal).where(ParametroFiscal.anio == 2024)
    res_params = await db.execute(stmt_params)
    param = res_params.scalar_one_or_none()
    
    # Obtener Tablas ISR para la periodicidad
    # Por ahora hardcodeamos periodicidad "04" (quincenal) si no tiene, u obtenemos la suya
    perio = contrato.periodicidad_pago_id if contrato.periodicidad_pago_id else "04"
    stmt_isr = select(TablaISR).where(TablaISR.anio == 2024, TablaISR.periodicidad == perio)
    res_isr = await db.execute(stmt_isr)
    tablas_isr = res_isr.scalars().all()
    
    # Cálculo ISR
    isr_retenido = 0.0
    if tablas_isr:
        for t in tablas_isr:
            if float(t.limite_inferior) <= ingreso_gravable <= float(t.limite_superior):
                excedente = ingreso_gravable - float(t.limite_inferior)
                impuesto_marginal = excedente * (float(t.porcentaje) / 100.0)
                isr_retenido = float(t.cuota_fija) + impuesto_marginal
                break
                
    # Cálculo IMSS (Cuota Obrero) aproximada (Enf y Mat, Inv y Vida, Cesantía) = ~2.375% del SBC
    # Para ser exactos, si SBC > 3 UMA, se paga un extra en Enf y Mat, pero usemos fórmula base para MVP.
    cuota_imss = (sbc * req.dias_periodo) * 0.02375
    
    total_percepciones = ingreso_gravable
    total_deducciones = (req.faltas * sd) + isr_retenido + cuota_imss
    neto = total_percepciones - total_deducciones
    
    return CalculoNominaResponse(
        ingreso_gravable=ingreso_gravable,
        isr_retenido=round(isr_retenido, 2),
        cuota_imss=round(cuota_imss, 2),
        total_percepciones=round(total_percepciones, 2),
        total_deducciones=round(total_deducciones, 2),
        neto_pagado=round(neto, 2)
    )

@router.get("/parametros-fiscales/{anio}", response_model=ParametroFiscalResponse)
async def get_parametros_fiscales(anio: int, db: AsyncSession = Depends(get_db)):
    stmt = select(ParametroFiscal).where(ParametroFiscal.anio == anio)
    res = await db.execute(stmt)
    param = res.scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail="Parámetros no encontrados para el año solicitado")
    return param

@router.get("/tablas-isr/{anio}", response_model=list[TablaISRResponse])
async def get_tablas_isr(anio: int, db: AsyncSession = Depends(get_db)):
    stmt = select(TablaISR).where(TablaISR.anio == anio).order_by(TablaISR.limite_inferior)
    res = await db.execute(stmt)
    return res.scalars().all()

# =================================================================
# CONTRATOS LABORALES
# =================================================================
@router.get("/empleados/{empleado_id}/contratos", response_model=List[ContratoLaboralResponse])
async def list_contratos(
    empleado_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(ContratoLaboral).where(
        ContratoLaboral.empleado_id == empleado_id,
        ContratoLaboral.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/contratos", response_model=ContratoLaboralResponse, status_code=status.HTTP_201_CREATED)
async def create_contrato(
    contrato: ContratoLaboralCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_contrato = ContratoLaboral(**contrato.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_contrato)
    await db.commit()
    await db.refresh(db_contrato)
    return db_contrato

# =================================================================
# CATÁLOGOS SAT NÓMINA CFDI 4.0
# =================================================================
@router.get("/catalogos/sat/percepciones", response_model=List[SATCatalogoResponse])
async def list_sat_percepciones(db: AsyncSession = Depends(get_db)):
    stmt = select(SATCatalogoPercepcion).where(SATCatalogoPercepcion.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/catalogos/sat/deducciones", response_model=List[SATCatalogoResponse])
async def list_sat_deducciones(db: AsyncSession = Depends(get_db)):
    stmt = select(SATCatalogoDeduccion).where(SATCatalogoDeduccion.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()
