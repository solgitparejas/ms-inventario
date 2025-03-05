import pytest
from flask import json
from app import create_app  # Asumiendo que tienes una fábrica de aplicaciones
from app.services import StockService
from unittest.mock import patch

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch.object(StockService, 'retirar')
def test_retirar_producto(mock_retirar, client):
    mock_retirar.return_value = {"id": 1, "producto": "Producto A", "cantidad": 2, "entrada_salida": "salida"}
    stock_data = {"producto": "Producto A", "cantidad": 2, "entrada_salida": "salida"}
    response = client.post("/inventarios/retirar", data=json.dumps(stock_data), content_type='application/json')
    
    assert response.status_code == 200
    assert response.json["id"] == 1
    mock_retirar.assert_called_once()

@patch.object(StockService, 'ingresar')
def test_ingresar_producto(mock_ingresar, client):
    mock_ingresar.return_value = {"id": 2, "producto": "Producto B", "cantidad": 5, "entrada_salida": "entrada"}
    stock_data = {"producto": "Producto B", "cantidad": 5, "entrada_salida": "entrada"}
    response = client.post("/inventarios/ingresar", data=json.dumps(stock_data), content_type='application/json')
    
    assert response.status_code == 200
    assert response.json["id"] == 2
    mock_ingresar.assert_called_once()
