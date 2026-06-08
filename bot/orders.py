import traceback
from typing import Optional
from bot.client import BinanceFuturesClient
from bot.exceptions import TradingBotError
from bot.logger import logger
from bot.models import OrderResponse
from bot.response_parser import parse_order_response
from bot.validators import validate_order_request


class OrderService:
    """Service to coordinate order validation, execution, response parsing, and error logging."""

    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    def execute_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderResponse:
        """Validates and executes an order, parsing the response.

        Logs errors with full tracebacks to the log file on failure.
        """
        logger.info(
            f"Pre-flight Order Setup | Symbol: {symbol} | Side: {side} | Type: {order_type} | Qty: {quantity}"
        )

        # 1. Run local validation checks before calling the remote API
        request_model = validate_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        logger.info(
            f"Validation Passed | Target: {request_model.symbol} | "
            f"Side: {request_model.side} | Type: {request_model.order_type}"
        )

        try:
            # 2. Call the Binance API via the client wrapper
            raw_response = self.client.place_order(
                symbol=request_model.symbol,
                side=request_model.side,
                order_type=request_model.order_type,
                quantity=request_model.quantity,
                price=request_model.price,
                stop_price=request_model.stop_price,
            )

            # 3. Parse and normalize the raw response
            logger.info("Order executed. Normalizing response payload...")
            parsed_response = parse_order_response(raw_response)

            logger.info(
                f"Order Complete | ID: {parsed_response.order_id} | "
                f"Status: {parsed_response.status} | AvgPrice: {parsed_response.avg_price}"
            )
            return parsed_response

        except TradingBotError as e:
            # Log full stack trace for all trading bot exceptions
            logger.error(
                f"Trading error occurred: {e}\nTraceback:\n{traceback.format_exc()}"
            )
            raise
        except Exception as e:
            # Catch unexpected exceptions and log traceback
            logger.error(
                f"Unexpected system error during execution: {e}\nTraceback:\n{traceback.format_exc()}"
            )
            raise TradingBotError(f"System execution failure: {e}")
