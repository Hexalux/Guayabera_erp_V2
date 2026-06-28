import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.core.database import async_session_maker, init_db
from app.models.tenant import Tenant
from app.models.inventory import CategoriaProductoTextil, ProductoTextil, Almacen, UbicacionAlmacen, LoteProducto, MovimientoInventario
from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza, Banco, MovimientoBancario
from app.models.hr import Empleado, ContratoLaboral, ControlVacaciones, Nomina
from app.models.production import OrdenProduccion, RecetaProduccion, CostoSubcontratacionMaquila
from app.models.branches import Sucursal, CajaRegistradora
from sqlalchemy import delete

# Mocking current user dependency
class MockUser:
    id = "test-user-id"
    email = "test@guayabera.com"
    tipo_usuario = "admin_empresa"
    tenant_id = "test-tenant-id"
    is_active = True

def mock_get_current_user():
    return MockUser()

app.dependency_overrides[get_current_user] = mock_get_current_user

# Prepara la base de datos antes de las pruebas
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    import asyncio
    
    async def _setup():
        await init_db()
        async with async_session_maker() as session:
            # Limpiar datos anteriores de prueba en orden de dependencias
            await session.execute(delete(MovimientoInventario).where(MovimientoInventario.tenant_id == "test-tenant-id"))
            await session.execute(delete(LoteProducto).where(LoteProducto.tenant_id == "test-tenant-id"))
            await session.execute(delete(ProductoTextil).where(ProductoTextil.tenant_id == "test-tenant-id"))
            await session.execute(delete(UbicacionAlmacen).where(UbicacionAlmacen.tenant_id == "test-tenant-id"))
            await session.execute(delete(Almacen).where(Almacen.tenant_id == "test-tenant-id"))
            
            await session.execute(delete(MovimientoPoliza).where(MovimientoPoliza.tenant_id == "test-tenant-id"))
            await session.execute(delete(PolizaContable).where(PolizaContable.tenant_id == "test-tenant-id"))
            await session.execute(delete(CuentaContable).where(CuentaContable.tenant_id == "test-tenant-id"))
            await session.execute(delete(Banco).where(Banco.tenant_id == "test-tenant-id"))
            
            await session.execute(delete(ControlVacaciones).where(ControlVacaciones.tenant_id == "test-tenant-id"))
            await session.execute(delete(Nomina).where(Nomina.tenant_id == "test-tenant-id"))
            await session.execute(delete(ContratoLaboral).where(ContratoLaboral.tenant_id == "test-tenant-id"))
            await session.execute(delete(Empleado).where(Empleado.tenant_id == "test-tenant-id"))
            
            await session.execute(delete(CostoSubcontratacionMaquila).where(CostoSubcontratacionMaquila.tenant_id == "test-tenant-id"))
            await session.execute(delete(OrdenProduccion).where(OrdenProduccion.tenant_id == "test-tenant-id"))
            await session.execute(delete(RecetaProduccion).where(RecetaProduccion.tenant_id == "test-tenant-id"))
            
            await session.execute(delete(Sucursal).where(Sucursal.tenant_id == "test-tenant-id"))
            await session.execute(delete(CategoriaProductoTextil).where(CategoriaProductoTextil.tenant_id == "test-tenant-id"))
            await session.execute(delete(Tenant).where(Tenant.id == "test-tenant-id"))
            
            await session.commit()

            # Insertar Tenant de prueba
            tenant = Tenant(
                id="test-tenant-id",
                name="Empresa de Prueba",
                subdomain="prueba",
                schema_name="prueba_schema",
                is_active=True
            )
            session.add(tenant)
            await session.commit()

            # Insertar Categoría de prueba
            categoria = CategoriaProductoTextil(
                id="test-category-id",
                nombre="Telas de Lino",
                codigo="CAT-LINO-01",
                tenant_id="test-tenant-id"
            )
            session.add(categoria)
            await session.commit()

    # Ejecutar la inicialización
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(_setup())
    else:
        asyncio.run(_setup())

def test_all_business_flows():
    with TestClient(app) as client:
        # ==========================================
        # 1. INVENTORY FLOW
        # ==========================================
        # Crear Almacén
        response = client.post("/api/v1/inventory/almacenes", json={
            "nombre": "Almacén Central Mérida",
            "codigo": "ALM-MID-01"
        })
        assert response.status_code == 201
        almacen = response.json()
        assert almacen["nombre"] == "Almacén Central Mérida"
        assert almacen["codigo"] == "ALM-MID-01"

        # Crear Ubicación (Odoo Style)
        response = client.post("/api/v1/inventory/ubicaciones", json={
            "almacen_id": almacen["id"],
            "nombre": "Pasillo A - Estante 1 - Rack 3 - Nivel 2",
            "pasillo": "A",
            "estante": "1",
            "rack": "3",
            "nivel": "2"
        })
        assert response.status_code == 201
        ubicacion = response.json()
        assert ubicacion["pasillo"] == "A"
        assert ubicacion["rack"] == "3"

        # Crear Producto
        response = client.post("/api/v1/inventory/productos", json={
            "nombre": "Guayabera Presidencial Lino Blanca",
            "sku": "GUAY-PRES-LINO-W",
            "categoria_id": "test-category-id",
            "tipo_producto": "producto_terminado"
        })
        assert response.status_code == 201

        # ==========================================
        # 2. FINANCE ACCOUNTING FLOW
        # ==========================================
        # Crear Cuenta Contable (CONTPAQi Style)
        response = client.post("/api/v1/finance/cuentas", json={
            "codigo": "101.01.001",
            "nombre": "Caja General Mérida",
            "nivel": 3,
            "tipo": "activo",
            "naturaleza": "deudora",
            "es_agrupadora": False
        })
        assert response.status_code == 201
        cuenta_caja = response.json()

        response = client.post("/api/v1/finance/cuentas", json={
            "codigo": "401.01.001",
            "nombre": "Ventas de Guayaberas Nacionales",
            "nivel": 3,
            "tipo": "ingresos",
            "naturaleza": "acreedora",
            "es_agrupadora": False
        })
        assert response.status_code == 201
        cuenta_ventas = response.json()

        # Crear Póliza Contable (Cuadrada)
        response = client.post("/api/v1/finance/polizas", json={
            "numero": 101,
            "tipo": "diario",
            "fecha": "2026-06-04",
            "descripcion": "Venta de 10 guayaberas de lino",
            "movimientos": [
                {
                    "cuenta_id": cuenta_caja["id"],
                    "cargo": 5500.0,
                    "abono": 0.0,
                    "concepto": "Ingreso por venta de guayaberas"
                },
                {
                    "cuenta_id": cuenta_ventas["id"],
                    "cargo": 0.0,
                    "abono": 5500.0,
                    "concepto": "Reconocimiento de ingresos de ventas"
                }
            ]
        })
        assert response.status_code == 201
        poliza = response.json()
        assert float(poliza["total_cargos"]) == 5500.0
        assert float(poliza["total_abonos"]) == 5500.0

        # ==========================================
        # 3. HR FLOW
        # ==========================================
        # Crear Empleado
        response = client.post("/api/v1/hr/empleados", json={
            "codigo": "EMP-009",
            "nombre_completo": "Juan Canché",
            "email": "juan.canche@guayabera.com",
            "rfc": "CACJ950515HM1",
            "curp": "CACJ950515HDFRRD02",
            "nss": "12345678901"
        })
        assert response.status_code == 201
        empleado = response.json()
        assert empleado["nombre_completo"] == "Juan Canché"

        # Registrar ruta del expediente digital
        response = client.post(f"/api/v1/hr/empleados/{empleado['id']}/documentos", json={
            "tipo_documento": "nacimiento",
            "archivo_path": "/var/uploads/documents/acta_juan.pdf"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # ==========================================
        # 4. CAD LICENSE VERIFICATION
        # ==========================================
        response = client.get("/api/v1/cad/licencia/verificar?codigo_licencia=TEST-1111-2222-3333")
        assert response.status_code in [200, 403]
