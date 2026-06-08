from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol, e.g., BTCUSDT")
    side: OrderSide = Field(..., description="BUY or SELL")
    order_type: OrderType = Field(..., alias="type", description="MARKET, LIMIT, or STOP_LIMIT")
    quantity: float = Field(..., description="Order quantity, must be > 0")
    price: Optional[float] = Field(None, description="Limit price. Required for LIMIT and STOP_LIMIT")
    stop_price: Optional[float] = Field(None, description="Stop price. Required for STOP_LIMIT")

    model_config = {
        "populate_by_name": True,
        "use_enum_values": True
    }


class OrderResponse(BaseModel):
    order_id: int
    client_order_id: str
    symbol: str
    status: str
    side: OrderSide
    order_type: OrderType
    price: float
    avg_price: float
    orig_qty: float
    executed_qty: float
    cumulative_quote: float
    time_in_force: str
    timestamp: int  # Transaction time in milliseconds

    model_config = {
        "use_enum_values": True
    }
