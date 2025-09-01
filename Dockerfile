# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application
COPY app.py .

# Expose port 5000
EXPOSE 5000

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash flaskuser
USER flaskuser

# Default command (overridden by docker-compose for development)
CMD ["python", "app.py"]