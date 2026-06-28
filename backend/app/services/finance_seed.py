from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import CuentaContable

# Catálogo base SAT Nivel 1 y 2
CATALOGO_SAT_BASE = [
    # ACTIVOS
    {"codigo": "100", "nombre": "Activo", "nivel": 1, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True},
    {"codigo": "101", "nombre": "Efectivo y equivalentes de efectivo", "nivel": 2, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "100"},
    {"codigo": "101.01", "nombre": "Caja", "nivel": 3, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": False, "parent_code": "101"},
    {"codigo": "102", "nombre": "Bancos", "nivel": 2, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "100"},
    {"codigo": "102.01", "nombre": "Bancos Nacionales", "nivel": 3, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": False, "parent_code": "102"},
    {"codigo": "105", "nombre": "Clientes", "nivel": 2, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "100"},
    {"codigo": "115", "nombre": "Inventario", "nivel": 2, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "100"},
    {"codigo": "150", "nombre": "Activo Fijo (Propiedad, Planta y Equipo)", "nivel": 2, "tipo": "activo", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "100"},
    
    # PASIVOS
    {"codigo": "200", "nombre": "Pasivo", "nivel": 1, "tipo": "pasivo", "naturaleza": "acreedora", "es_agrupadora": True},
    {"codigo": "201", "nombre": "Proveedores", "nivel": 2, "tipo": "pasivo", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "200"},
    {"codigo": "205", "nombre": "Acreedores Diversos", "nivel": 2, "tipo": "pasivo", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "200"},
    {"codigo": "216", "nombre": "Impuestos por pagar", "nivel": 2, "tipo": "pasivo", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "200"},
    
    # CAPITAL
    {"codigo": "300", "nombre": "Capital Contable", "nivel": 1, "tipo": "capital", "naturaleza": "acreedora", "es_agrupadora": True},
    {"codigo": "301", "nombre": "Capital Social", "nivel": 2, "tipo": "capital", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "300"},
    {"codigo": "304", "nombre": "Resultados de Ejercicios Anteriores", "nivel": 2, "tipo": "capital", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "300"},
    {"codigo": "305", "nombre": "Resultado del Ejercicio", "nivel": 2, "tipo": "capital", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "300"},
    
    # INGRESOS
    {"codigo": "400", "nombre": "Ingresos", "nivel": 1, "tipo": "ingresos", "naturaleza": "acreedora", "es_agrupadora": True},
    {"codigo": "401", "nombre": "Ingresos por Ventas", "nivel": 2, "tipo": "ingresos", "naturaleza": "acreedora", "es_agrupadora": True, "parent_code": "400"},
    
    # COSTOS
    {"codigo": "500", "nombre": "Costos", "nivel": 1, "tipo": "costos", "naturaleza": "deudora", "es_agrupadora": True},
    {"codigo": "501", "nombre": "Costo de Ventas", "nivel": 2, "tipo": "costos", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "500"},
    
    # GASTOS
    {"codigo": "600", "nombre": "Gastos", "nivel": 1, "tipo": "gastos", "naturaleza": "deudora", "es_agrupadora": True},
    {"codigo": "601", "nombre": "Gastos Generales", "nivel": 2, "tipo": "gastos", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "600"},
    {"codigo": "602", "nombre": "Gastos de Venta", "nivel": 2, "tipo": "gastos", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "600"},
    {"codigo": "603", "nombre": "Gastos de Administración", "nivel": 2, "tipo": "gastos", "naturaleza": "deudora", "es_agrupadora": True, "parent_code": "600"},
]

async def seed_sat_catalog(db: AsyncSession, tenant_id: str):
    """
    Precarga el catálogo de cuentas nivel 1 y 2 (y algunas base nivel 3)
    para un nuevo tenant.
    """
    cuentas_dict = {}
    
    # Proceso en orden para que las agrupadoras existan antes que las hijas (basado en el array estático ordenado)
    for cta_data in CATALOGO_SAT_BASE:
        parent_id = None
        if "parent_code" in cta_data:
            parent_code = cta_data["parent_code"]
            if parent_code in cuentas_dict:
                parent_id = cuentas_dict[parent_code]
        
        nueva_cuenta = CuentaContable(
            tenant_id=tenant_id,
            codigo=cta_data["codigo"],
            nombre=cta_data["nombre"],
            nivel=cta_data["nivel"],
            tipo=cta_data["tipo"],
            naturaleza=cta_data["naturaleza"],
            es_agrupadora=cta_data["es_agrupadora"],
            cuenta_padre_id=parent_id
        )
        db.add(nueva_cuenta)
        await db.flush() # flush para obtener el ID generado inmediatamente
        
        cuentas_dict[cta_data["codigo"]] = nueva_cuenta.id
    
    # Después de insertar todas, commit
    await db.commit()
