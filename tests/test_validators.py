import pytest
from bot.exceptions import ValidationError
from bot.models import OrderSide, OrderType
from bot.validators import validate_order_request, validate_symbol


def test_validate_symbol_valid():
    assert validate_symbol("BTCUSDT") == "BTCUSDT"
    assert validate_symbol("ethusdt") == "ETHUSDT"
    assert validate_symbol("1000SHIBUSDT") == "1000SHIBUSDT"


def test_validate_symbol_invalid():
    with pytest.raises(ValidationError, match="required"):
        validate_symbol("")

    with pytest.raises(ValidationError, match="alphanumeric"):
        validate_symbol("BTC_USDT")

    with pytest.raises(ValidationError, match="USDT-M Futures contracts"):
        validate_symbol("BTCFDUSD")

    with pytest.raises(ValidationError, match="3-16 characters"):
        # Too short or too long
        validate_symbol("AB")
        validate_symbol("A" * 17)


def test_validate_order_request_market_success():
    req = validate_order_request(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.05
    )
    assert req.symbol == "BTCUSDT"
    assert req.side == OrderSide.BUY
    assert req.order_type == OrderType.MARKET
    assert req.quantity == 0.05
    assert req.price is None
    assert req.stop_price is None


def test_validate_order_request_limit_success():
    req = validate_order_request(
        symbol="ETHUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity=1.2,
        price=3500.5
    )
    assert req.symbol == "ETHUSDT"
    assert req.side == OrderSide.SELL
    assert req.order_type == OrderType.LIMIT
    assert req.quantity == 1.2
    assert req.price == 3500.5


def test_validate_order_request_limit_missing_price():
    with pytest.raises(ValidationError, match="Price is required for LIMIT orders"):
        validate_order_request(
            symbol="ETHUSDT",
            side="SELL",
            order_type="LIMIT",
            quantity=1.2
        )


def test_validate_order_request_stop_limit_success():
    req = validate_order_request(
        symbol="BTCUSDT",
        side="BUY",
        order_type="STOP_LIMIT",
        quantity=0.01,
        price=68000.0,
        stop_price=67500.0
    )
    assert req.symbol == "BTCUSDT"
    assert req.side == OrderSide.BUY
    assert req.order_type == OrderType.STOP_LIMIT
    assert req.quantity == 0.01
    assert req.price == 68000.0
    assert req.stop_price == 67500.0


def test_validate_order_request_stop_limit_missing_params():
    # Missing price
    with pytest.raises(ValidationError, match="Price is required for STOP_LIMIT"):
        validate_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="STOP_LIMIT",
            quantity=0.01,
            stop_price=67500.0
        )

    # Missing stop price
    with pytest.raises(ValidationError, match="Stop price is required for STOP_LIMIT"):
        validate_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="STOP_LIMIT",
            quantity=0.01,
            price=68000.0
        )


def test_validate_order_request_invalid_quantity():
    with pytest.raises(ValidationError, match="Quantity must be greater than zero"):
        validate_order_request("BTCUSDT", "BUY", "MARKET", quantity=-0.01)

    with pytest.raises(ValidationError, match="Quantity must be greater than zero"):
        validate_order_request("BTCUSDT", "BUY", "MARKET", quantity=0.0)


def test_validate_order_request_invalid_side_or_type():
    with pytest.raises(ValidationError, match="Invalid order side"):
        validate_order_request("BTCUSDT", "HOLD", "MARKET", quantity=1.0)

    with pytest.raises(ValidationError, match="Invalid order type"):
        validate_order_request("BTCUSDT", "BUY", "TRAILING_STOP", quantity=1.0)
