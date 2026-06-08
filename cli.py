import sys
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bot.config import load_config
from bot.client import BinanceFuturesClient
from bot.orders import OrderService
from bot.exceptions import TradingBotError, ConfigError
from bot.validators import validate_order_request
from bot.logger import setup_logger, logger
from bot.helpers import format_timestamp

# Create Typer app and Rich Console
app = typer.Typer(
    help="PrimeTrade Trading Bot CLI for Binance Futures Testnet",
    add_completion=False
)
console = Console()

# Initialize Logger (Default to INFO)
setup_logger("INFO")


def display_request_summary(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None, stop_price: Optional[float] = None):
    """Displays the standard order request layout."""
    console.print("\n[bold blue]------------------------------------[/]")
    console.print("[bold white]ORDER REQUEST[/]")
    console.print("[bold blue]------------------------------------[/]")
    console.print(f"Symbol      [bold cyan]{symbol}[/]")
    console.print(f"Side        [bold yellow]{side}[/]")
    console.print(f"Type        [bold yellow]{order_type}[/]")
    console.print(f"Quantity    {quantity}")
    if price is not None:
        console.print(f"Price       {price}")
    if stop_price is not None:
        console.print(f"Stop Price  {stop_price}")
    console.print()


def display_response_summary(order_id: int, status: str, executed_qty: float, avg_price: float):
    """Displays the standard order response layout."""
    console.print("[bold green]------------------------------------[/]")
    console.print("[bold white]ORDER RESPONSE[/]")
    console.print("[bold green]------------------------------------[/]")
    console.print(f"Order ID        {order_id}")
    console.print(f"Status          [bold green]{status}[/]")
    console.print(f"Executed Qty    {executed_qty}")
    console.print(f"Average Price   {avg_price}")
    console.print()
    console.print("[bold green]✔ Trade completed successfully.[/]")


def run_order_placement(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None
):
    """Executes the order pipeline with validation, loader spinner, and response printing."""
    # 1. First run pre-flight local validations
    try:
        validate_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
    except TradingBotError as e:
        console.print(f"[bold red]❌ Input Validation Error:[/] {e}")
        return

    # 2. Display Request
    display_request_summary(symbol, side, order_type, quantity, price, stop_price)

    # 3. Load configurations and API Client
    try:
        config = load_config()
        client = BinanceFuturesClient(
            api_key=config.binance_api_key.get_secret_value(),
            secret_key=config.binance_secret_key.get_secret_value(),
            use_testnet=config.binance_use_testnet
        )
        service = OrderService(client)
    except ConfigError as ce:
        console.print(f"[bold red]❌ Configuration Error:[/] {ce}")
        console.print("[bold yellow]⚠️  Please create/modify your .env file with valid credentials.[/]")
        return
    except Exception as e:
        console.print(f"[bold red]❌ Client Init Error:[/] {e}")
        return

    # 4. Execute with Progress spinner
    response = None
    try:
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold yellow]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task(description="Submitting...", total=None)
            response = service.execute_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
    except TradingBotError as tbe:
        console.print(f"[bold red]❌ Execution Failed:[/] {tbe}")
        return
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected Error:[/] {e}")
        return

    # 5. Display response
    if response:
        display_response_summary(
            order_id=response.order_id,
            status=response.status,
            executed_qty=response.executed_qty,
            avg_price=response.avg_price
        )


def show_configuration():
    """Prints masked active configuration parameters."""
    console.print("\n[bold cyan]=== Current Bot Configuration ===[/]")
    try:
        config = load_config()
        console.print(f"Binance Base URL:   [yellow]{config.binance_base_url}[/]")
        console.print(f"Use Testnet:        [yellow]{config.binance_use_testnet}[/]")
        console.print(f"API Key:            [green]{config.get_masked_api_key()}[/]")
        console.print(f"Secret Key:         [green]{config.get_masked_secret_key()}[/]")
        console.print(f"Log Level:          [green]{config.log_level}[/]")

        # Testnet check
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Pinging Testnet server..."),
                transient=True,
                console=console
            ) as progress:
                progress.add_task("", total=None)
                client = BinanceFuturesClient(
                    api_key=config.binance_api_key.get_secret_value(),
                    secret_key=config.binance_secret_key.get_secret_value(),
                    use_testnet=config.binance_use_testnet
                )
                srv_time = client.get_server_time()
            console.print(f"Connection Status:  [bold green]CONNECTED ✅[/]")
            console.print(f"Server Time (UTC):  [green]{format_timestamp(srv_time)}[/]")
        except Exception as conn_err:
            console.print(f"Connection Status:  [bold red]DISCONNECTED ❌ ({conn_err})[/]")

    except ConfigError as ce:
        console.print(f"[bold red]❌ Config Error:[/] {ce}")
        console.print("[bold yellow]⚠️  Please double check that a .env file exists and contains valid keys.[/]")


def run_dry_run_validation():
    """Prompts for input and performs local validation checks without placing any orders."""
    console.print("\n[bold magenta]=== Input Validation (Dry Run) ===[/]")
    symbol = console.input("Symbol (e.g. BTCUSDT): ").strip()
    side = console.input("Side (BUY/SELL): ").strip()
    order_type = console.input("Order Type (MARKET/LIMIT/STOP_LIMIT): ").strip()

    qty_str = console.input("Quantity: ").strip()
    try:
        qty = float(qty_str) if qty_str else 0.0
    except ValueError:
        qty = -1.0

    price = None
    if order_type.upper() in ("LIMIT", "STOP_LIMIT"):
        price_str = console.input("Price: ").strip()
        try:
            price = float(price_str) if price_str else None
        except ValueError:
            price = -1.0

    stop_price = None
    if order_type.upper() == "STOP_LIMIT":
        sp_str = console.input("Stop Price: ").strip()
        try:
            stop_price = float(sp_str) if sp_str else None
        except ValueError:
            stop_price = -1.0

    try:
        validate_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=price,
            stop_price=stop_price
        )
        console.print("[bold green]✔ Parameters are valid and ready for submission.[/]")
    except TradingBotError as e:
        console.print(f"[bold red]❌ Validation Rejected:[/] {e}")


def interactive_menu_loop():
    """Loops and displays the main interactive terminal menu."""
    while True:
        console.print("\n[bold cyan]=========================[/]")
        console.print("[bold cyan]PrimeTrade Trading Bot[/]")
        console.print("[bold cyan]=========================[/]")
        console.print("1 [green]Place Order[/]")
        console.print("2 [green]View Configuration[/]")
        console.print("3 [green]Validate Inputs[/]")
        console.print("4 [red]Exit[/]")

        choice = console.input("\nSelect Option: ").strip()

        if choice == "1":
            # Place Order
            symbol = console.input("Symbol (e.g. BTCUSDT): ").strip()
            side = console.input("Side (BUY/SELL): ").strip()
            order_type = console.input("Order Type (MARKET/LIMIT/STOP_LIMIT): ").strip()

            qty_str = console.input("Quantity: ").strip()
            try:
                qty = float(qty_str) if qty_str else 0.0
            except ValueError:
                console.print("[bold red]❌ Quantity must be a valid number.[/]")
                continue

            price = None
            if order_type.upper() in ("LIMIT", "STOP_LIMIT"):
                price_str = console.input("Price: ").strip()
                try:
                    price = float(price_str) if price_str else None
                except ValueError:
                    console.print("[bold red]❌ Price must be a valid number.[/]")
                    continue

            stop_price = None
            if order_type.upper() == "STOP_LIMIT":
                sp_str = console.input("Stop Price: ").strip()
                try:
                    stop_price = float(sp_str) if sp_str else None
                except ValueError:
                    console.print("[bold red]❌ Stop Price must be a valid number.[/]")
                    continue

            run_order_placement(symbol, side, order_type, qty, price, stop_price)

        elif choice == "2":
            show_configuration()
        elif choice == "3":
            run_dry_run_validation()
        elif choice == "4" or choice.lower() == "exit":
            console.print("[bold yellow]Exiting PrimeTrade Trading Bot. Goodbye![/]")
            sys.exit(0)
        else:
            console.print("[bold red]❌ Invalid option. Choose 1, 2, 3 or 4.[/]")


@app.command()
def execute(
    symbol: Optional[str] = typer.Option(None, "--symbol", help="Trading Symbol (e.g. BTCUSDT)"),
    side: Optional[str] = typer.Option(None, "--side", help="BUY or SELL"),
    order_type: Optional[str] = typer.Option(None, "--type", help="MARKET, LIMIT, or STOP_LIMIT"),
    quantity: Optional[float] = typer.Option(None, "--quantity", help="Order quantity (e.g. 0.01)"),
    price: Optional[float] = typer.Option(None, "--price", help="Limit order entry price"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="Trigger price for stop limit orders")
):
    """Entry point check: Runs interactive menu if no arguments are passed, else runs direct order placement."""
    # Check if any options are provided. If not, open interactive menu.
    if symbol is None and side is None and order_type is None and quantity is None:
        interactive_menu_loop()
    else:
        # Check required fields for direct arguments
        if not symbol or not side or not order_type or quantity is None:
            console.print(
                "[bold red]❌ Error: When using CLI flags, you must provide --symbol, --side, --type, and --quantity.[/]"
            )
            raise typer.Exit(code=1)

        run_order_placement(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )


if __name__ == "__main__":
    app()
