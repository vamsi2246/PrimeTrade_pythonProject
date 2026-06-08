import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Adjust path to import bot modules
sys.path.append(str(Path(__file__).resolve().parent))

from bot.config import load_config
from bot.client import BinanceFuturesClient
from bot.orders import OrderService
from bot.exceptions import TradingBotError, ConfigError
from bot.helpers import format_timestamp

# 1. Page Configuration (Premium styling and wide layout)
st.set_page_config(
    page_title="PrimeTrade Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Theme and Premium Aesthetics
st.markdown("""
<style>
    /* Dark Theme Base Styling */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    
    /* Title Styling */
    .dashboard-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
    }
    
    .dashboard-subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card Container */
    .status-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    .status-header {
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #94A3B8;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    .status-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    /* Log block formatting */
    .log-container {
        font-family: 'Courier New', Courier, monospace;
        background-color: #050B14;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 15px;
        max-height: 400px;
        overflow-y: auto;
        color: #38BDF8;
        font-size: 0.85rem;
        white-space: pre-wrap;
    }
    
    /* Streamlit overrides */
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #60A5FA 0%, #2563EB 100%);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State for Orders placed in this session
if "orders_history" not in st.session_state:
    st.session_state.orders_history = []


# 2. Setup Configuration and Client
@st.cache_resource(show_spinner=False)
def get_trading_service():
    """Initializes the Binance client using local config."""
    config = load_config()
    client = BinanceFuturesClient(
        api_key=config.binance_api_key.get_secret_value(),
        secret_key=config.binance_secret_key.get_secret_value(),
        use_testnet=config.binance_use_testnet
    )
    return client, OrderService(client), config


try:
    client, service, config = get_trading_service()
    config_loaded = True
except ConfigError as ce:
    config_loaded = False
    config_error_msg = str(ce)
except Exception as e:
    config_loaded = False
    config_error_msg = f"Failed to initialize client: {e}"


# Tailing helper
def get_recent_logs(num_lines=30):
    log_path = Path(__file__).resolve().parent / "logs" / "trading.log"
    if not log_path.exists():
        return "No activity logs available yet. Make a trade to initiate logging."
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            return "".join(lines[-num_lines:])
    except Exception as e:
        return f"Error reading logs: {e}"


# 3. Main Dashboard Layout
st.markdown("<h1 class='dashboard-title'>⚡ PrimeTrade</h1>", unsafe_allow_html=True)
st.markdown("<p class='dashboard-subtitle'>Binance USDT-M Futures Testnet Local Control Dashboard</p>", unsafe_allow_html=True)

if not config_loaded:
    st.error("⚠️ Configuration Error")
    st.info(f"Details: {config_error_msg}")
    st.warning("Please verify your `.env` file exists at the root of this workspace and contains valid keys.")
    st.stop()

# Header status checks
col_status1, col_status2, col_status3, col_status4 = st.columns(4)

# Ping Server
is_connected = False
server_time_str = "N/A"
try:
    srv_time = client.get_server_time()
    is_connected = True
    server_time_str = format_timestamp(srv_time)
except Exception:
    is_connected = False

with col_status1:
    status_indicator = "🟢 ACTIVE" if is_connected else "🔴 OFFLINE"
    st.markdown(
        f"<div class='status-card'><div class='status-header'>Network Connection</div><div class='status-value'>{status_indicator}</div></div>",
        unsafe_allow_html=True
    )

with col_status2:
    st.markdown(
        f"<div class='status-card'><div class='status-header'>Environment Mode</div><div class='status-value'>{'Futures Testnet' if config.binance_use_testnet else 'Futures Mainnet'}</div></div>",
        unsafe_allow_html=True
    )

with col_status3:
    st.markdown(
        f"<div class='status-card'><div class='status-header'>Masked API Key</div><div class='status-value'>{config.get_masked_api_key()}</div></div>",
        unsafe_allow_html=True
    )

with col_status4:
    st.markdown(
        f"<div class='status-card'><div class='status-header'>Server Time (Local)</div><div class='status-value' style='font-size: 1.1rem; padding-top: 8px;'>{server_time_str}</div></div>",
        unsafe_allow_html=True
    )

# Sidebar Form for Placement
st.sidebar.markdown("### 📥 Place New Order")
symbol_input = st.sidebar.text_input("Symbol (e.g. BTCUSDT)", value="BTCUSDT").strip().upper()
side_input = st.sidebar.selectbox("Order Side", ["BUY", "SELL"])
type_input = st.sidebar.selectbox("Order Type", ["MARKET", "LIMIT", "STOP_LIMIT"])

quantity_input = st.sidebar.number_input("Quantity", min_value=0.0, step=0.001, format="%.4f")

price_input = None
if type_input in ("LIMIT", "STOP_LIMIT"):
    price_input = st.sidebar.number_input("Limit Price", min_value=0.0, step=0.1, format="%.2f")

stop_price_input = None
if type_input == "STOP_LIMIT":
    stop_price_input = st.sidebar.number_input("Stop (Trigger) Price", min_value=0.0, step=0.1, format="%.2f")

submit_btn = st.sidebar.button("Execute Trade Order")

# Handle Order submission
if submit_btn:
    if quantity_input <= 0:
        st.sidebar.error("❌ Quantity must be greater than 0.")
    else:
        try:
            with st.spinner("Submitting order..."):
                response = service.execute_order(
                    symbol=symbol_input,
                    side=side_input,
                    order_type=type_input,
                    quantity=quantity_input,
                    price=price_input,
                    stop_price=stop_price_input
                )
            
            st.success(f"✔ Order Placed: ID {response.order_id} ({response.status})")
            
            # Store in session state for displaying in recent orders table
            st.session_state.orders_history.insert(0, {
                "Timestamp": format_timestamp(response.timestamp),
                "Symbol": response.symbol,
                "Side": response.side,
                "Type": response.order_type,
                "Price": response.price if response.price > 0 else "MARKET",
                "Avg Price": response.avg_price,
                "Qty": response.orig_qty,
                "Status": response.status,
                "Order ID": response.order_id
            })
        except TradingBotError as tbe:
            st.error(f"❌ Execution Failure: {tbe}")
        except Exception as e:
            st.error(f"❌ Unexpected Error: {e}")

# Main body divided into two panels
col_main_left, col_main_right = st.columns([3, 2])

with col_main_left:
    st.markdown("### 📋 Recent Placed Orders (Current Session)")
    if st.session_state.orders_history:
        df = pd.DataFrame(st.session_state.orders_history)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders placed during this browser session. Use the left sidebar to execute trades.")

    # Account Balance Check
    st.markdown("### 💰 Account Balance Info")
    if is_connected:
        try:
            with st.spinner("Fetching balance..."):
                acc_info = client.get_account_info()
            
            # Get asset balances with balance > 0
            assets = []
            for asset in acc_info.get("assets", []):
                wallet_bal = float(asset.get("walletBalance", 0.0))
                unrealized_pnl = float(asset.get("unrealizedProfit", 0.0))
                margin_bal = float(asset.get("marginBalance", 0.0))
                if wallet_bal > 0 or margin_bal > 0:
                    assets.append({
                        "Asset": asset.get("asset"),
                        "Wallet Balance": wallet_bal,
                        "Margin Balance": margin_bal,
                        "Unrealized PnL": unrealized_pnl
                    })
            
            if assets:
                st.table(pd.DataFrame(assets))
            else:
                st.info("No balances found (account balance is zero).")
        except Exception as e:
            st.error(f"Failed to fetch account balance: {e}")
    else:
        st.warning("Cannot fetch balances while offline.")

with col_main_right:
    st.markdown("### 🪵 Live Trading Logs (`logs/trading.log`)")
    
    # Auto-refresh log option
    auto_refresh = st.checkbox("Auto-refresh Logs", value=True)
    
    logs_content = get_recent_logs()
    st.markdown(f"<div class='log-container'>{logs_content}</div>", unsafe_allow_html=True)
    
    if auto_refresh:
        # A simple rerun button to refresh state
        st.button("🔄 Refresh Data")
