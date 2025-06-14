# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app first
COPY . .

# Install Node dependencies
RUN npm install

# Build Tailwind CSS with all files available
RUN npx tailwindcss -i ./app/static/css/src/main.css -o ./app/static/css/dist/main.css --minify

# Expose FastAPI port
EXPOSE 5000

# Set environment variables for FastAPI/Uvicorn
ENV PYTHONPATH=/app

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"] 