# FinWave Backend Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment for headless xlwings
ENV XLWINGS_HEADLESS=1

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for templates
RUN pip install --no-cache-dir \
    pandas \
    openpyxl \
    xlsxwriter \
    requests \
    python-dateutil

# Copy application code
COPY . .

# Generate template on build
RUN cd templates && python -m make_templates

# Create non-root user
RUN useradd -m -u 1000 finwave && chown -R finwave:finwave /app
USER finwave

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]