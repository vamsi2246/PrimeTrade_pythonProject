# Use an official Python slim runtime as a parent image
FROM python:3.12-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set the working directory inside the container
WORKDIR /app

# Install lightweight system dependencies (curl for healthchecks, git for streamlit indicators)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install Python package dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create directory for persisted logs
RUN mkdir -p logs

# Expose Streamlit dashboard port
EXPOSE 8501

# Healthcheck to verify the web interface status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default execution is to start the Streamlit Dashboard
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
