FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and port_common module
COPY main.py .
COPY port_common/ ./port_common/

# Set the entrypoint
ENTRYPOINT ["python", "main.py"]
