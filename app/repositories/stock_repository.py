from app import db
from app.models import Stock

class StockRepository:
    
    
    def save(self, stock: Stock) -> Stock:
        db.session.add(stock)
        db.session.commit()
        return stock

    def get_stock_by_producto(self, producto_id: int) -> Stock:
        return db.session.query(Stock).filter_by(producto=producto_id).first()