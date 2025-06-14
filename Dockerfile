# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Build Pandoc from source (this is the "hack" stage)
# =============================================================================
FROM haskell:9.4-slim as pandoc-builder

# Install system dependencies for building Pandoc
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    zlib1g-dev \
    liblua5.3-dev \
    libffi-dev \
    libgmp-dev \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up Stack with optimized settings for Docker
RUN stack config set system-ghc --global true
RUN stack config set install-ghc --global false

# HACK: Pre-install common dependencies to leverage Docker layer caching
# This speeds up subsequent builds significantly
RUN stack setup --resolver lts-21.17

# Clone Pandoc repository (using specific stable version)
WORKDIR /pandoc-build
RUN git clone --depth 1 --branch 3.1.8 https://github.com/jgm/pandoc.git .

# HACK: Modify stack.yaml for faster builds in Docker environment
RUN echo "docker:" >> stack.yaml && \
    echo "  enable: false" >> stack.yaml && \
    echo "ghc-options:" >> stack.yaml && \
    echo "  \"\$everything\": -O1" >> stack.yaml

# HACK: Use system resolver and optimize for container builds
RUN stack build --resolver lts-21.17 \
    --ghc-options="-j4 +RTS -A64m -n2m -RTS" \
    --fast \
    --copy-bins \
    --local-bin-path /usr/local/bin/ \
    pandoc

# Verify pandoc was built correctly
RUN pandoc --version

# =============================================================================
# Stage 2: Main application image
# =============================================================================
FROM python:3.11-slim

# Install Node.js, npm, and system dependencies for the application
RUN apt-get update && \
    apt-get install -y \
    curl \
    build-essential \
    liblua5.3-0 \
    zlib1g \
    libffi8 \
    libgmp10 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# HACK: Copy the built pandoc binary from the builder stage
COPY --from=pandoc-builder /usr/local/bin/pandoc /usr/local/bin/pandoc

# Verify pandoc works in the final image
RUN pandoc --version

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

# Create necessary directories for plugin data
RUN mkdir -p /app/data/chains /app/data/templates

# Expose FastAPI port
EXPOSE 5000

# Set environment variables for FastAPI/Uvicorn
ENV PYTHONPATH=/app
ENV PANDOC_VERSION=3.1.8-custom

# Health check to ensure pandoc is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pandoc --version && curl -f http://localhost:5000/api/plugins || exit 1

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"] 