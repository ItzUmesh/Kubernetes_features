FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Ensure Python output is not buffered; useful for logs in containers
ENV PYTHONUNBUFFERED=1

# Copy deps first to leverage Docker layer caching during development
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Expose the port the Flask app listens on
EXPOSE 5000

# Use gunicorn for a production-friendly WSGI server. One worker
# is sufficient for this small example; increase for real workloads.
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
