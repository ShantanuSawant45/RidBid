# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - gdal-bin & libgdal-dev: Required for Django PostGIS (geo-spatial queries)
# - build-essential & libpq-dev: Required for compiling psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django project
COPY . /app/

# Expose port 8000
EXPOSE 8000

# The default command will run Daphne (ASGI server for WebSockets and HTTP)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
