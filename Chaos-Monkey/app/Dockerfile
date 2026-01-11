FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app source
COPY app.py .

# Expose the port the app listens on
EXPOSE 8080

# Use Gunicorn for a production-style server in the container
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "2"]
