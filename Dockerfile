FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including fontconfig and freetype for font management
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    fontconfig \
    libfreetype6 \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install fonts
COPY fonts/ /usr/share/fonts/truetype/teko/
RUN fc-cache -f -v

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Reinstall Pillow to ensure it's compiled with freetype support
RUN pip uninstall -y Pillow && pip install --no-cache-dir Pillow

# Copy entire project structure (API, db, app, testing)
COPY API/ ./API/
COPY db/ ./db/
COPY app/ ./app/
# COPY testing/ ./testing/

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FLASK_APP=app/backend/src/main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Health check using curl (more reliable in Docker)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run Flask application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
