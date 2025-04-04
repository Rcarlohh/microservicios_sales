from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.types import DECIMAL  
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Venta(Base):
    __tablename__ = "ventas"

    id_venta = Column(Integer, primary_key=True, index=True)
    fecha_venta = Column(DateTime, default=datetime.utcnow, nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(String(50), nullable=False)
    sucursal = Column(Integer, ForeignKey('sucursales.id_sucursal'), nullable=True)
    empleado_venta = Column(Integer, ForeignKey('empleados.id_empleado'), nullable=True)
    estado = Column(Enum('Completada', 'Cancelada', 'Reembolsada'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    empleado = relationship("Empleado", back_populates="ventas")
    sucursal_rel = relationship("Sucursal", back_populates="ventas")
    detalles_venta = relationship("DetalleVenta", back_populates="venta_rel")


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"

    id_detalle = Column(Integer, primary_key=True, index=True)
    venta = Column(Integer, ForeignKey('ventas.id_venta', ondelete="CASCADE"), nullable=False)
    producto = Column(Integer, ForeignKey('productos.id_producto', ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    venta_rel = relationship("Venta", back_populates="detalles_venta")

class Producto(Base):
    __tablename__ = "Productos"

    id_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    precio = Column(DECIMAL(10, 2), nullable=False)

    # Relaciones
    detalles_venta = relationship("DetalleVenta", back_populates="producto_rel")
