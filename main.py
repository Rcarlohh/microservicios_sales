# main.py
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uvicorn
import crud
import models
import schemas
from database import SessionLocal, engine
import socket
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tortilleria_sales.log')
    ]
)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tortilleria Sales Microservice")

# Función para obtener la IP pública
def get_public_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error obteniendo IP pública: {e}")
        return "IP_NO_DISPONIBLE"

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    public_ip = get_public_ip()
    logger.info(f" Servicio de Ventas Tortillería iniciado")
    logger.info(f" IP Pública: {public_ip}")
    logger.info(" Endpoints disponibles:")
    logger.info(f"- POST 54.145.241.91:8000/ventas/ (Crear Venta)")
    logger.info(f"- GET 54.145.241.91:8000/ventas/ (Listar Ventas)")
    logger.info(f"- GET 54.145.241.91:8000/ventas/{{venta_id}} (Obtener Venta Específica)")
    logger.info(f"- GET 54.145.241.91:8000/ventas/periodo/ (Obtener Ventas por Periodo)")
    logger.info(" Documentación de API disponible en: /docs")

@app.post("/ventas/", response_model=schemas.Venta)
def crear_venta(venta: schemas.VentaCreate, db: Session = Depends(get_db)):
    logger.info(f"Intento de crear venta: {venta}")
    try:
        venta_creada = crud.crear_venta(db=db, venta=venta)
        logger.info(f"Venta creada exitosamente. ID: {venta_creada.id_venta}")
        return venta_creada
    except Exception as e:
        logger.error(f"Error al crear venta: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/ventas/", response_model=list[schemas.Venta])
def listar_ventas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Listando ventas. Skip: {skip}, Limit: {limit}")
    ventas = crud.obtener_ventas(db, skip=skip, limit=limit)
    logger.info(f"Total de ventas listadas: {len(ventas)}")
    return ventas

@app.get("/ventas/{venta_id}", response_model=schemas.Venta)
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    logger.info(f"Buscando venta con ID: {venta_id}")
    db_venta = crud.obtener_venta_por_id(db, venta_id=venta_id)
    if db_venta is None:
        logger.warning(f"Venta no encontrada. ID: {venta_id}")
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    logger.info(f"Venta encontrada: {db_venta.id_venta}")
    return db_venta

@app.get("/ventas/periodo/", response_model=list[schemas.Venta])
def obtener_ventas_por_periodo(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db)
):
    logger.info(f"Buscando ventas entre {fecha_inicio} y {fecha_fin}")
    ventas = crud.obtener_ventas_por_periodo(db, fecha_inicio, fecha_fin)
    logger.info(f"Total de ventas en el periodo: {len(ventas)}")
    return ventas

@app.get("/ventas/resumen/total/")
def obtener_total_ventas_periodo(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db)
):
    logger.info(f"Calculando total de ventas entre {fecha_inicio} y {fecha_fin}")
    total = crud.obtener_total_ventas_por_periodo(db, fecha_inicio, fecha_fin)
    logger.info(f"Total de ventas en el periodo: ${total}")
    return {"total_ventas": total}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)