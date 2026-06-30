
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.core_services import MotorContableBridge, TimbradoCFDI, CalculadoraTextil

router = APIRouter()

@router.post("/produccion/orden/{id}/finalizar")
def finalizar_orden(id: int, db: Session = Depends(get_db)):
    asiento = MotorContableBridge.generar_asiento_por_movimiento_inventario({"id": id})
    return {"mensaje": "Orden finalizada", "asiento_generado": asiento}

@router.post("/fiscal/timbrar")
def timbrar_factura(datos: dict):
    resultado = TimbradoCFDI.timbrar_comprobante("xml", "cert", "key")
    return {"status": "timbrado", "uuid": resultado["uuid"]}

@router.get("/textil/conversion")
def convertir_unidades(kg: float, gramaje: float):
    res = CalculadoraTextil.convertir_kg_a_piezas(kg, gramaje)
    return res
