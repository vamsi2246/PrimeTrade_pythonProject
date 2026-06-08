# PrimeTrade Deployment Guide

This guide provides instructions for deploying the PrimeTrade Bot and Dashboard across various environments.

---

## 1. Local Setup (Development & CLI)

### Prerequisites
- Python 3.12+
- Git

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/vamsi2246/PrimeTrade_pythonProject.git
   cd PrimeTrade_pythonProject
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your Binance Futures Testnet credentials:
   ```ini
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_SECRET_KEY=your_testnet_secret_key
   BINANCE_USE_TESTNET=True
   ```
   *Note: Never commit your `.env` file to version control. It is ignored in `.gitignore`.*

### Running the Application
**CLI Mode:**
```bash
python cli.py
```

**Dashboard Mode (Streamlit):**
```bash
streamlit run streamlit_app.py
```

---

## 2. Docker Deployment

Docker provides an isolated environment for the application, ensuring consistency across different systems.

### Prerequisites
- Docker
- Docker Compose

### Building and Running
1. Build the image:
   ```bash
   docker build -t trading-bot .
   ```
2. Run the container (passing the environment file):
   ```bash
   docker run --env-file .env -p 8501:8501 trading-bot
   ```
   This exposes the Streamlit dashboard on port 8501.

**Using Docker Compose:**
You can also use docker-compose for a streamlined startup:
```bash
docker-compose up --build
```

---

## 3. Streamlit Cloud Deployment

Streamlit Cloud is the easiest way to host the interactive dashboard for portfolio presentation.

1. Push your repository to GitHub.
2. Log in to [Streamlit Cloud](https://share.streamlit.io/).
3. Click **New app**.
4. Select your GitHub repository, branch (`main`), and main file path (`streamlit_app.py`).
5. **CRITICAL:** Before clicking Deploy, configure your Secrets:
   - Click **Advanced settings**.
   - Under **Secrets**, add the contents of your `.env` file:
     ```toml
     BINANCE_API_KEY = "your_actual_api_key_here"
     BINANCE_SECRET_KEY = "your_actual_secret_key_here"
     BINANCE_USE_TESTNET = true
     ```
6. Click **Deploy!**

*Note: The included `.streamlit/config.toml` configures a matching dark theme and enables headless mode automatically.*

---

## 4. Render Deployment

Render offers an excellent platform for deploying the dashboard as a web service.

### Infrastructure as Code (render.yaml)
The repository includes a `render.yaml` blueprint.

1. Log in to [Render](https://dashboard.render.com/).
2. Go to **Blueprints** and click **New Blueprint Instance**.
3. Connect your GitHub repository.
4. Render will automatically detect the `render.yaml` file and configure the service.
5. **CRITICAL:** Before the deployment succeeds, you must provide your secrets:
   - Go to your newly created Web Service settings.
   - Navigate to **Environment**.
   - Add the missing Environment Variables:
     - `BINANCE_API_KEY`
     - `BINANCE_SECRET_KEY`
6. Trigger a manual deploy if necessary. Render automatically manages the port binding via the `$PORT` variable injected into the start command.

---

## 5. Troubleshooting

**"Configuration Error: Missing API keys"**
Ensure your `.env` file is named correctly (not `.env.txt`) and is in the root directory. If on a cloud provider, ensure Environment Variables/Secrets are set.

**"Network Error: Connection Timeout"**
Ensure you have outgoing internet access. If using Docker, ensure the network mode allows outbound HTTP traffic.

**"BinanceAPIError: Invalid API Key"**
Verify you are using *Testnet* keys if `BINANCE_USE_TESTNET=True`. Mainnet keys will not work on Testnet, and vice versa.

---

## Security Best Practices
- The `.gitignore` prevents accidentally pushing `.env` files.
- The `.dockerignore` prevents baking secrets or local caches into Docker images.
- Always use the Secrets management feature of your cloud provider (Streamlit Secrets, Render Environment Variables) instead of hardcoding keys in your codebase.
