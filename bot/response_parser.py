from typing import Any, Dict
from bot.exceptions import ValidationError
from bot.models import OrderResponse, OrderSide, OrderType


def parse_order_response(raw: Dict[str, Any]) -> OrderResponse:
    """Parses raw dict response from Binance Futures API into OrderResponse model.

    Handles field normalization, string-to-float conversions, and camelCase mapping.
    """
    try:
        order_id = raw.get("orderId")
        if order_id is None:
            raise ValidationError("Missing 'orderId' in Binance order response.")

        client_order_id = raw.get("clientOrderId", "")
        symbol = raw.get("symbol", "")
        status = raw.get("status", "")

        side_val = raw.get("side", "")
        try:
            side = OrderSide(side_val)
        except ValueError:
            raise ValidationError(f"Unknown side '{side_val}' in API response.")

        type_val = raw.get("type", "")
        try:
            order_type = OrderType(type_val)
        except ValueError:
            raise ValidationError(f"Unknown type '{type_val}' in API response.")

        price = float(raw.get("price", 0.0))
        orig_qty = float(raw.get("origQty", 0.0))
        executed_qty = float(raw.get("executedQty", 0.0))
        cum_quote = float(raw.get("cumQuote", 0.0))

        avg_price = float(raw.get("avgPrice", 0.0))
        if avg_price == 0.0 and executed_qty > 0.0:
            avg_price = cum_quote / executed_qty

        time_in_force = raw.get("timeInForce", "GTC")

        timestamp = raw.get("updateTime") or raw.get("time")
        if timestamp is None:
            raise ValidationError("Missing timestamp fields in Binance response.")

        return OrderResponse(
            order_id=int(order_id),
            client_order_id=client_order_id,
            symbol=symbol,
            status=status,
            side=side,
            order_type=order_type,
            price=price,
            avg_price=avg_price,
            orig_qty=orig_qty,
            executed_qty=executed_qty,
            cumulative_quote=cum_quote,
            time_in_force=time_in_force,
            timestamp=int(timestamp),
        )
    except ValidationError:
        raise
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Failed to parse Binance response due to format mismatch: {e}")

