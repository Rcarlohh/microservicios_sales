from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, DECIMAL, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicialización de Flask
app = Flask(__name__)

# Configuración de la conexión a la base de datos usando variables de entorno o valores predeterminados
# Utilizamos una cadena de conexión de ejemplo que será reemplazada en producción
db_user = os.environ.get('DB_USER', 'admin')
db_password = os.environ.get('DB_PASSWORD', 'Sam2102$')  # Nunca usar contraseñas directamente en el código
db_host = os.environ.get('DB_HOST', 'database-1.cc924m0us98a.us-east-1.rds.amazonaws.com')
db_name = os.environ.get('DB_NAME', 'tortilleria')

# Configuración de SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# Inicialización de SQLAlchemy
db = SQLAlchemy(app)


# Modelos de base de datos
class Sucursal(db.Model):
    __tablename__ = 'Sucursal'

    id_sucursal = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    direccion = db.Column(db.String(255))
    ventas = db.relationship('Venta', backref='sucursal_rel')


class Empleado(db.Model):
    __tablename__ = 'Empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    ventas = db.relationship('Venta', backref='empleado_rel')


class Producto(db.Model):
    __tablename__ = 'Productos'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.DECIMAL(10, 2))
    detalles_venta = db.relationship('DetalleVenta', backref='producto_rel')


class Venta(db.Model):
    __tablename__ = 'ventas'

    id_venta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_venta = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    total = db.Column(db.DECIMAL(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)
    sucursal = db.Column(db.Integer, db.ForeignKey('Sucursal.id_sucursal'))
    empleado_venta = db.Column(db.Integer, db.ForeignKey('Empleados.id_empleado'))
    estado = db.Column(db.Enum('Completada', 'Cancelada', 'Reembolsada'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    detalles = db.relationship('DetalleVenta', backref='venta_rel', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id_venta': self.id_venta,
            'fecha_venta': self.fecha_venta.strftime('%Y-%m-%d %H:%M:%S') if self.fecha_venta else None,
            'total': float(self.total) if self.total else 0,
            'metodo_pago': self.metodo_pago,
            'sucursal': self.sucursal,
            'empleado_venta': self.empleado_venta,
            'estado': self.estado,
            'detalles': [detalle.to_dict() for detalle in self.detalles]
        }


class DetalleVenta(db.Model):
    __tablename__ = 'Detalles_venta'

    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'))
    producto = db.Column(db.Integer, db.ForeignKey('Productos.id_producto'))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.DECIMAL(10, 2), nullable=False)
    subtotal = db.Column(db.DECIMAL(10, 2), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def to_dict(self):
        return {
            'id_detalle': self.id_detalle,
            'venta': self.venta,
            'producto': self.producto,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario) if self.precio_unitario else 0,
            'subtotal': float(self.subtotal) if self.subtotal else 0
        }


# Rutas de la API

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar si el servicio está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Servicio operativo'}), 200


@app.route('/ventas', methods=['GET'])
def obtener_ventas():
    """Obtener todas las ventas"""
    try:
        ventas = Venta.query.all()
        return jsonify({
            'status': 'success',
            'data': [venta.to_dict() for venta in ventas],
            'count': len(ventas)
        }), 200
    except Exception as e:
        logger.error(f"Error al obtener ventas: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error al obtener ventas'}), 500


@app.route('/ventas/<int:venta_id>', methods=['GET'])
def obtener_venta(venta_id):
    """Obtener una venta específica por ID"""
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({'status': 'error', 'message': 'Venta no encontrada'}), 404

        return jsonify({
            'status': 'success',
            'data': venta.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error al obtener venta {venta_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al obtener venta {venta_id}'}), 500


@app.route('/ventas', methods=['POST'])
def crear_venta():
    """Crear una nueva venta con sus detalles"""
    try:
        datos = request.json

        if not datos or not isinstance(datos, dict):
            return jsonify({'status': 'error', 'message': 'Datos inválidos'}), 400

        # Validar datos requeridos para la venta
        if not all(key in datos for key in ['total', 'metodo_pago', 'sucursal', 'empleado_venta', 'estado']):
            return jsonify({'status': 'error', 'message': 'Faltan datos requeridos para la venta'}), 400

        # Validar que existan detalles
        if 'detalles' not in datos or not isinstance(datos['detalles'], list) or len(datos['detalles']) == 0:
            return jsonify({'status': 'error', 'message': 'Se requiere al menos un detalle de venta'}), 400

        # Iniciar transacción
        try:
            # Crear la venta
            nueva_venta = Venta(
                fecha_venta=datetime.now(),
                total=datos['total'],
                metodo_pago=datos['metodo_pago'],
                sucursal=datos['sucursal'],
                empleado_venta=datos['empleado_venta'],
                estado=datos['estado']
            )

            db.session.add(nueva_venta)
            db.session.flush()  # Para obtener el ID de la venta

            # Crear detalles de venta
            for detalle_datos in datos['detalles']:
                if not all(key in detalle_datos for key in ['producto', 'cantidad', 'precio_unitario', 'subtotal']):
                    raise ValueError('Datos incompletos en detalle de venta')

                nuevo_detalle = DetalleVenta(
                    venta=nueva_venta.id_venta,
                    producto=detalle_datos['producto'],
                    cantidad=detalle_datos['cantidad'],
                    precio_unitario=detalle_datos['precio_unitario'],
                    subtotal=detalle_datos['subtotal']
                )

                db.session.add(nuevo_detalle)

            # Confirmar transacción
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Venta creada exitosamente',
                'data': nueva_venta.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error en transacción de venta: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Error al procesar la venta: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Error general al crear venta: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error al crear la venta'}), 500


@app.route('/ventas/<int:venta_id>', methods=['PUT'])
def actualizar_venta(venta_id):
    """Actualizar una venta existente"""
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({'status': 'error', 'message': 'Venta no encontrada'}), 404

        datos = request.json

        if not datos or not isinstance(datos, dict):
            return jsonify({'status': 'error', 'message': 'Datos inválidos'}), 400

        # Actualizar datos de la venta
        if 'total' in datos:
            venta.total = datos['total']
        if 'metodo_pago' in datos:
            venta.metodo_pago = datos['metodo_pago']
        if 'sucursal' in datos:
            venta.sucursal = datos['sucursal']
        if 'empleado_venta' in datos:
            venta.empleado_venta = datos['empleado_venta']
        if 'estado' in datos:
            venta.estado = datos['estado']

        # Actualizar detalles si se proporcionan
        if 'detalles' in datos and isinstance(datos['detalles'], list):
            # Eliminar detalles existentes y crear nuevos
            DetalleVenta.query.filter_by(venta=venta_id).delete()

            for detalle_datos in datos['detalles']:
                if not all(key in detalle_datos for key in ['producto', 'cantidad', 'precio_unitario', 'subtotal']):
                    return jsonify({'status': 'error', 'message': 'Datos incompletos en detalle de venta'}), 400

                nuevo_detalle = DetalleVenta(
                    venta=venta_id,
                    producto=detalle_datos['producto'],
                    cantidad=detalle_datos['cantidad'],
                    precio_unitario=detalle_datos['precio_unitario'],
                    subtotal=detalle_datos['subtotal']
                )

                db.session.add(nuevo_detalle)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Venta actualizada exitosamente',
            'data': venta.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar venta {venta_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al actualizar la venta: {str(e)}'}), 500


@app.route('/ventas/<int:venta_id>', methods=['DELETE'])
def eliminar_venta(venta_id):
    """Eliminar una venta y sus detalles"""
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({'status': 'error', 'message': 'Venta no encontrada'}), 404

        # La eliminación en cascada de detalles está configurada en la relación
        db.session.delete(venta)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Venta {venta_id} eliminada exitosamente'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar venta {venta_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al eliminar la venta: {str(e)}'}), 500


@app.route('/ventas/por-fecha', methods=['GET'])
def ventas_por_fecha():
    """Obtener ventas filtradas por fecha"""
    try:
        fecha_inicio = request.args.get('inicio')
        fecha_fin = request.args.get('fin')

        if not fecha_inicio or not fecha_fin:
            return jsonify({'status': 'error', 'message': 'Se requieren las fechas de inicio y fin'}), 400

        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400

        # Agregar un día a la fecha fin para incluir todo el día
        fecha_fin = datetime(fecha_fin.year, fecha_fin.month, fecha_fin.day, 23, 59, 59)

        ventas = Venta.query.filter(Venta.fecha_venta.between(fecha_inicio, fecha_fin)).all()

        return jsonify({
            'status': 'success',
            'data': [venta.to_dict() for venta in ventas],
            'count': len(ventas)
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener ventas por fecha: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al obtener ventas por fecha: {str(e)}'}), 500


@app.route('/ventas/por-sucursal/<int:sucursal_id>', methods=['GET'])
def ventas_por_sucursal(sucursal_id):
    """Obtener ventas filtradas por sucursal"""
    try:
        ventas = Venta.query.filter_by(sucursal=sucursal_id).all()

        return jsonify({
            'status': 'success',
            'data': [venta.to_dict() for venta in ventas],
            'count': len(ventas)
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener ventas por sucursal {sucursal_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al obtener ventas por sucursal: {str(e)}'}), 500


@app.route('/detalles-venta/<int:venta_id>', methods=['GET'])
def obtener_detalles_venta(venta_id):
    """Obtener detalles de una venta específica"""
    try:
        detalles = DetalleVenta.query.filter_by(venta=venta_id).all()

        if not detalles:
            return jsonify(
                {'status': 'warning', 'message': 'No se encontraron detalles para esta venta', 'data': []}), 200

        return jsonify({
            'status': 'success',
            'data': [detalle.to_dict() for detalle in detalles],
            'count': len(detalles)
        }), 200

    except Exception as e:
        logger.error(f"Error al obtener detalles de venta {venta_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al obtener detalles de venta: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint no encontrado'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'status': 'error', 'message': 'Método no permitido'}), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'status': 'error', 'message': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    # Configuración para permitir conexiones desde cualquier IP en el puerto 8080
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))

    # Crear tablas si no existen (solo para desarrollo)
    with app.app_context():
        db.create_all()

    # Iniciar la aplicación
    app.run(host=host, port=port, debug=False)