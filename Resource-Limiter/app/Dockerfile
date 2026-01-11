# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app directly so process exit restarts container
CMD ["python", "app.py"]
