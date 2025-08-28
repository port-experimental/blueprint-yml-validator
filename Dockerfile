FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire
COPY . .

# Set the entrypoint
ENTRYPOINT ["python", "main.py"]
CMD ["./"]

