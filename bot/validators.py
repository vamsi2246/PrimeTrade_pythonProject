import re
from typing import Optional
from bot.exceptions import ValidationError
from bot.models import OrderRequest, OrderSide, OrderType

# Regular expression for Binance USDT-M Futures symbols (e.g. BTCUSDT, 1000SHIBUSDT)
SYMBOL_REGEX = re.compile(r"^[A-Z0-9]{3,16}$")


def validate_symbol(symbol: Optional[str]) -> str:
    """Validates that the symbol matches the format and ends with USDT for USDT-M Futures."""
    if not symbol:
        raise ValidationError("Symbol is required and cannot be empty.")

    clean_symbol = symbol.strip().upper()

    if not SYMBOL_REGEX.match(clean_symbol):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. Symbol must be alphanumeric, 3-16 characters long."
        )

    if not clean_symbol.endswith("USDT"):
        raise ValidationError(
            f"Invalid symbol: '{symbol}'. Bot only supports USDT-M Futures contracts (must end with 'USDT')."
        )

    return clean_symbol


def validate_order_request(
    symbol: Optional[str],
    side: Optional[str],
    order_type: Optional[str],
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> OrderRequest:
    """Performs validation on raw input fields, returning a validated OrderRequest.

    Raises ValidationError on violations.
    """
    # 1. Validate Symbol
    valid_symbol = validate_symbol(symbol)

    # 2. Validate Side
    if not side:
        raise ValidationError("Order side (BUY/SELL) is required.")

    side_upper = side.strip().upper()
    try:
        valid_side = OrderSide(side_upper)
    except ValueError:
        allowed = [s.value for s in OrderSide]
        raise ValidationError(
            f"Invalid order side: '{side}'. Must be one of: {', '.join(allowed)}."
        )

    # 3. Validate Order Type
    if not order_type:
        raise ValidationError("Order type (MARKET/LIMIT/STOP_LIMIT) is required.")

    type_upper = order_type.strip().upper()
    try:
        valid_type = OrderType(type_upper)
    except ValueError:
        allowed = [t.value for t in OrderType]
        raise ValidationError(
            f"Invalid order type: '{order_type}'. Must be one of: {', '.join(allowed)}."
        )

    # 4. Validate Quantity
    if quantity <= 0:
        raise ValidationError(f"Quantity must be greater than zero. Provided: {quantity}")

    # 5. Validate Price (Required for LIMIT and STOP_LIMIT)
    if valid_type in (OrderType.LIMIT, OrderType.STOP_LIMIT):
        if price is None:
            raise ValidationError(f"Price is required for {valid_type.value} orders.")
        if price <= 0:
            raise ValidationError(
                f"Price must be greater than zero for {valid_type.value} orders. Provided: {price}"
            )

    # 6. Validate Stop Price (Required for STOP_LIMIT)
    if valid_type == OrderType.STOP_LIMIT:
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        if stop_price <= 0:
            raise ValidationError(
                f"Stop price must be greater than zero for STOP_LIMIT orders. Provided: {stop_price}"
            )

    return OrderRequest(
        symbol=valid_symbol,
        side=valid_side,
        type=valid_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )
