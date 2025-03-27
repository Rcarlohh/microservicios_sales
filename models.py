# models.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.types import DECIMAL  # Importa Decimal correctamente
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Venta(Base):
    __tablename__ = "ventas"

    id_venta = Column(Integer, primary_key=True, index=True)
    fecha_venta = Column(DateTime, default=datetime.utcnow)
    total = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(String(50), nullable=False)
    sucursal = Column(Integer, ForeignKey('Sucursal.id_sucursal'), nullable=True)
    empleado_venta = Column(Integer, ForeignKey('Empleados.id_empleado'), nullable=True)
    estado = Column(Enum('Completada', 'Cancelada', 'Reembolsada'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    detalles_venta = relationship("DetalleVenta", back_populates="venta_rel")


class DetalleVenta(Base):
    __tablename__ = "Detalles_venta"

    id_detalle = Column(Integer, primary_key=True, index=True)
    venta = Column(Integer, ForeignKey('ventas.id_venta'))
    producto = Column(Integer, ForeignKey('Productos.id_producto'))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    venta_rel = relationship("Venta", back_populates="detalles_venta")