# crud.py
from sqlalchemy.orm import Session
import models
import schemas
from sqlalchemy import func
from datetime import datetime

def crear_venta(db: Session, venta: schemas.VentaCreate):
    # Crear venta principal
    db_venta = models.Venta(
        total=venta.total,
        metodo_pago=venta.metodo_pago,
        sucursal=venta.sucursal,
        empleado_venta=venta.empleado_venta,
        estado=venta.estado
    )
    db.add(db_venta)
    db.flush()  # Obtener ID de la venta

    # Crear detalles de venta
    for detalle in venta.detalles_venta:
        db_detalle = models.DetalleVenta(
            venta=db_venta.id_venta,
            producto=detalle.producto,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
            subtotal=detalle.subtotal
        )
        db.add(db_detalle)

    db.commit()
    db.refresh(db_venta)
    return db_venta

def obtener_ventas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Venta).offset(skip).limit(limit).all()

def obtener_venta_por_id(db: Session, venta_id: int):
    return db.query(models.Venta).filter(models.Venta.id_venta == venta_id).first()

def obtener_ventas_por_periodo(db: Session, inicio: datetime, fin: datetime):
    return db.query(models.Venta).filter(
        models.Venta.fecha_venta.between(inicio, fin)
    ).all()

def obtener_total_ventas_por_periodo(db: Session, inicio: datetime, fin: datetime):
    return db.query(func.sum(models.Venta.total)).filter(
        models.Venta.fecha_venta.between(inicio, fin)
    ).scalar() or 0