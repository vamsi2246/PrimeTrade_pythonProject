import pytest
from bot.exceptions import ValidationError
from bot.models import OrderSide, OrderType
from bot.response_parser import parse_order_response


def test_parse_order_response_market_filled():
    raw_payload = {
        "orderId": 123456789,
        "clientOrderId": "test_cli_01",
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "side": "BUY",
        "type": "MARKET",
        "price": "0.00",
        "avgPrice": "108200.15",
        "origQty": "0.01",
        "executedQty": "0.01",
        "cumQty": "0.01",
        "cumQuote": "1082.0015",
        "timeInForce": "GTC",
        "updateTime": 1612345678901
    }
    
    response = parse_order_response(raw_payload)
    
    assert response.order_id == 123456789
    assert response.client_order_id == "test_cli_01"
    assert response.symbol == "BTCUSDT"
    assert response.status == "FILLED"
    assert response.side == OrderSide.BUY
    assert response.order_type == OrderType.MARKET
    assert response.price == 0.0
    assert response.avg_price == 108200.15
    assert response.orig_qty == 0.01
    assert response.executed_qty == 0.01
    assert response.cumulative_quote == 1082.0015
    assert response.time_in_force == "GTC"
    assert response.timestamp == 1612345678901


def test_parse_order_response_limit_new():
    raw_payload = {
        "orderId": 987654321,
        "clientOrderId": "test_cli_02",
        "symbol": "ETHUSDT",
        "status": "NEW",
        "side": "SELL",
        "type": "LIMIT",
        "price": "3500.00",
        "avgPrice": "0.00",
        "origQty": "1.500",
        "executedQty": "0.000",
        "cumQty": "0.000",
        "cumQuote": "0.0000",
        "timeInForce": "GTC",
        "updateTime": 1612345679000
    }
    
    response = parse_order_response(raw_payload)
    
    assert response.order_id == 987654321
    assert response.status == "NEW"
    assert response.side == OrderSide.SELL
    assert response.order_type == OrderType.LIMIT
    assert response.price == 3500.0
    assert response.avg_price == 0.0
    assert response.orig_qty == 1.5
    assert response.executed_qty == 0.0
    assert response.cumulative_quote == 0.0
    assert response.time_in_force == "GTC"


def test_parse_order_response_avg_price_computation():
    # If avgPrice is "0.00" but executedQty > 0, avg_price should be computed from cumQuote / executedQty
    raw_payload = {
        "orderId": 55555,
        "clientOrderId": "test_cli_03",
        "symbol": "SOLUSDT",
        "status": "PARTIALLY_FILLED",
        "side": "BUY",
        "type": "MARKET",
        "price": "0.00",
        "avgPrice": "0.00",
        "origQty": "10.0",
        "executedQty": "5.0",
        "cumQty": "5.0",
        "cumQuote": "750.0",
        "timeInForce": "GTC",
        "updateTime": 1612345679500
    }
    
    response = parse_order_response(raw_payload)
    assert response.avg_price == 150.0  # 750.0 / 5.0


def test_parse_order_response_missing_fields():
    # Missing orderId
    invalid_payload = {
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "updateTime": 1612345678901
    }
    with pytest.raises(ValidationError, match="orderId"):
        parse_order_response(invalid_payload)

    # Missing timestamp
    invalid_payload2 = {
        "orderId": 123,
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "side": "BUY",
        "type": "MARKET"
    }
    with pytest.raises(ValidationError, match="timestamp"):
        parse_order_response(invalid_payload2)


def test_parse_order_response_invalid_enums():
    invalid_payload = {
        "orderId": 123,
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "side": "HOLD",  # Invalid side
        "type": "MARKET",
        "updateTime": 1612345678901
    }
    with pytest.raises(ValidationError, match="Unknown side"):
        parse_order_response(invalid_payload)
