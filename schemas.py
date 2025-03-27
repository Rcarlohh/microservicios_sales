# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class DetalleVentaBase(BaseModel):
    producto: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

class DetalleVentaCreate(DetalleVentaBase):
    pass

class DetalleVenta(DetalleVentaBase):
    id_detalle: int
    venta: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VentaBase(BaseModel):
    total: Decimal
    metodo_pago: str
    sucursal: Optional[int] = None
    empleado_venta: Optional[int] = None
    estado: str

class VentaCreate(VentaBase):
    detalles_venta: List[DetalleVentaCreate]

class Venta(VentaBase):
    id_venta: int
    fecha_venta: datetime
    created_at: datetime
    updated_at: datetime
    detalles_venta: List[DetalleVenta] = []

    class Config:
        from_attributes = True