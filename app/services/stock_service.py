import redis
from redis.lock import Lock
from datetime import datetime
from app import db, cache
from app.models import Stock
from app.repositories import StockRepository
import logging

repository = StockRepository()

class StockService:

    def __init__(self):
        # Conexión a Redis con host, puerto y contraseña especificados
        self.redis_client = redis.StrictRedis(
            host='docker-redis-1', 
            port=6379, 
            db=0, 
            password='Qvv3r7y'  
        )
        self.lock_timeout = 7 

    def retirar(self, stock: Stock) -> Stock:
        result = None
        if stock is not None:
            stock.fecha_transaccion = stock.fecha_transaccion if stock.fecha_transaccion else datetime.now()
            stock.entrada_salida = 2  # Salida de inventario
            lock_key = f"lock:producto:{stock.producto}"

            try:
                # Intentar adquirir el lock (bloqueo) durante un tiempo limitado
                with Lock(self.redis_client, lock_key, timeout=self.lock_timeout):
                    logging.info(f"Lock adquirido para el producto ID {stock.producto}")

                    # Verificar el stock disponible directamente desde la base de datos
                    current_stock = self._get_current_stock(stock.producto)

                    if current_stock < stock.cantidad:
                        raise ValueError(f"Stock insuficiente para el producto {stock.producto}. Disponible: {current_stock}, requerido: {stock.cantidad}")

                    # Registrar la salida del stock en la base de datos
                    result = repository.save(stock)

                    # Actualizar el caché después de la transacción
                    cache.delete(f'stock_{stock.producto}')  # Invalidar el caché antiguo
                    cache.set(f'stock_{stock.producto}', result, timeout=60)  # Actualizar caché con el nuevo stock

            except Exception as e:
                logging.error(f"Error durante la operación de retiro de producto: {e}")
                raise

        return result

    def _get_current_stock(self, producto_id: int) -> float:
        """
        Obtiene el stock actual directamente desde la base de datos.
        """
        query = """
            SELECT SUM(CASE WHEN entrada_salida = 1 THEN cantidad ELSE -cantidad END) AS stock_actual
            FROM inventarios
            WHERE producto_id = :producto_id
        """
        # Ejecutar la consulta correctamente usando 'text'
        result = db.session.execute(db.text(query), {"producto_id": producto_id}).fetchone()

        # Si no hay transacciones para este producto, considera el stock como 0
        return result.stock_actual if result.stock_actual is not None else 0

    def ingresar(self, stock: Stock) -> Stock:
        result = None
        if stock is not None:
            stock.fecha_transaccion = stock.fecha_transaccion if stock.fecha_transaccion else datetime.now()
            stock.entrada_salida = 1  # Entrada de inventario
            lock_key = f"lock:producto:{stock.producto}"

            try:
                # Intentar adquirir el lock (bloqueo) durante un tiempo limitado
                with Lock(self.redis_client, lock_key, timeout=self.lock_timeout):
                    logging.info(f"Lock adquirido para el producto ID {stock.producto}")

                    # Registrar la entrada del stock en la base de datos
                    result = repository.save(stock)

                    # Actualizar el caché después de la transacción
                    cache.delete(f'stock_{stock.producto}')  # Invalidar el caché antiguo
                    cache.set(f'stock_{stock.producto}', result, timeout=60)  # Actualizar caché con el nuevo stock

            except Exception as e:
                logging.error(f"Error durante la operación de ingreso de producto: {e}")
                raise

        return result