import time
from typing import Any, Dict, Optional
from binance.client import Client as BinanceClient
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from bot.exceptions import BinanceAPIError, NetworkError, OrderPlacementError
from bot.logger import logger, log_api_call
from bot.models import OrderType


class BinanceFuturesClient:
    """Production-grade client wrapper for Binance Futures Testnet API.

    Handles connection, request signing, exceptions, retries, and latency tracking.
    """

    def __init__(self, api_key: str, secret_key: str, use_testnet: bool = True):
        self._api_key = api_key
        self._secret_key = secret_key
        self._use_testnet = use_testnet

        # Initialize the underlying python-binance client
        try:
            self.client = BinanceClient(
                api_key=self._api_key,
                api_secret=self._secret_key,
                testnet=self._use_testnet
            )
        except Exception as e:
            logger.error(f"Failed to initialize underlying Binance client: {e}")
            raise ConnectionError(f"Binance client initialization failed: {e}")

    def _execute_api_call(self, func_name: str, api_func, *args, **kwargs) -> Dict[str, Any]:
        """Executes an API call with latency measurement, logging, and retry logic."""
        retry_state = {"count": 0}

        def before_sleep_callback(retry_state_info):
            retry_state["count"] = retry_state_info.attempt_number
            logger.warning(
                f"Retrying Binance API call: {func_name} | "
                f"Attempt {retry_state_info.attempt_number} after "
                f"{retry_state_info.next_action.sleep:.2f}s due to error: "
                f"{retry_state_info.outcome.exception()}"
            )

        # Retry only network-related failures
        @retry(
            retry=retry_if_exception_type(NetworkError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            before_sleep=before_sleep_callback,
            reraise=True
        )
        def _call_with_retry():
            start_time = time.perf_counter()
            payload = {"args": args, "kwargs": kwargs}
            try:
                response = api_func(*args, **kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                log_api_call(
                    endpoint=func_name,
                    payload=payload,
                    response=response,
                    latency_ms=latency_ms,
                    retry_count=retry_state["count"]
                )
                return response
            except BinanceAPIException as e:
                # API errors mean Binance received the call but rejected it (bad parameters, balance etc.)
                # We should NOT retry these
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                log_api_call(
                    endpoint=func_name,
                    payload=payload,
                    error=str(e),
                    latency_ms=latency_ms,
                    retry_count=retry_state["count"]
                )
                raise BinanceAPIError(
                    message=e.message,
                    status_code=e.status_code,
                    error_code=e.code
                )
            except (BinanceRequestException, RequestException, TimeoutError) as e:
                # Network or connection issues - we raise NetworkError to trigger retry
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                log_api_call(
                    endpoint=func_name,
                    payload=payload,
                    error=f"Network error: {e}",
                    latency_ms=latency_ms,
                    retry_count=retry_state["count"]
                )
                raise NetworkError(f"Network error while connecting to Binance: {e}")
            except Exception as e:
                # Unexpected exceptions
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                log_api_call(
                    endpoint=func_name,
                    payload=payload,
                    error=f"Unexpected error: {e}",
                    latency_ms=latency_ms,
                    retry_count=retry_state["count"]
                )
                raise OrderPlacementError(f"An unexpected error occurred: {e}")

        return _call_with_retry()

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """Places an order on Binance Futures (USDT-M).

        Maps internal STOP_LIMIT enum values to the appropriate exchange API format.
        """
        # Map our STOP_LIMIT to binance STOP order type
        binance_type = order_type
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
        }

        if order_type == OrderType.MARKET:
            params["type"] = "MARKET"
        elif order_type == OrderType.LIMIT:
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = time_in_force
        elif order_type == OrderType.STOP_LIMIT:
            params["type"] = "STOP"  # Binance Futures STOP type with price is STOP-LIMIT
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        return self._execute_api_call(
            func_name="futures_create_order",
            api_func=self.client.futures_create_order,
            **params
        )

    def get_account_info(self) -> Dict[str, Any]:
        """Fetches account information (balances, positions)."""
        return self._execute_api_call(
            func_name="futures_account",
            api_func=self.client.futures_account
        )

    def get_server_time(self) -> int:
        """Pings the Binance server to fetch system time and test connectivity."""
        response = self._execute_api_call(
            func_name="futures_time",
            api_func=self.client.futures_time
        )
        return response.get("serverTime", 0)
