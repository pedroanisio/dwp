# PDF to HTML Converter Plugin

This plugin converts PDF documents to HTML format using pdf2htmlEX, preserving layout, fonts, and vector graphics.

## 🏗️ Architecture

The plugin uses a **container orchestration architecture** with Docker socket communication:

```
┌─────────────────┐    ┌──────────────────────┐
│  Main App       │    │  pdf2htmlex-service  │
│  (Neural Plugin │◄──►│  (Conversion Service)│
│   System)       │    │                      │
│                 │    │                      │
│ + Docker CLI    │    │                      │
│ + Docker Socket │    │                      │
└─────────────────┘    └──────────────────────┘
         │                        │
         │                        │
         └────────────────────────┘
              Shared Volume
              (/app/shared)
```

## 🔧 How it Works

1. **File Upload**: User uploads PDF via web interface
2. **Shared Storage**: PDF saved to shared volume (`/app/shared`)
3. **Container Discovery**: Main app uses Docker API to find `pdf2htmlex-service`
4. **Service Communication**: Main app executes `docker exec` on sidecar container
5. **Conversion**: pdf2htmlEX processes PDF inside sidecar container
6. **Result Retrieval**: HTML file retrieved from shared volume
7. **Download**: Converted HTML made available for download

## 🐳 Docker Socket Requirements

This plugin requires **Docker socket access** for container communication:

```yaml
# docker-compose.yml
web:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Required for container communication
```

The main application container needs:
- Docker CLI installed
- Docker socket mounted
- Access to execute commands in the pdf2htmlex-service container

## 🚀 Starting the Services

```bash
# Start all services including pdf2htmlex-service
docker compose up -d

# Check service status
docker compose ps

# View pdf2htmlEX service logs
docker compose logs pdf2htmlex-service
```

## 🔍 Troubleshooting

### Service Not Available
```bash
# Check if pdf2htmlex-service is running
docker compose ps pdf2htmlex-service

# Restart the service
docker compose restart pdf2htmlex-service

# Check logs for errors
docker compose logs pdf2htmlex-service
```

### Docker Socket Issues
```bash
# Verify Docker socket is mounted
docker exec web ls -la /var/run/docker.sock

# Test Docker CLI access from web container
docker exec web docker ps

# Check if web container can find pdf2htmlex service
docker exec web docker ps --filter "name=pdf2htmlex-service"
```

### Container Communication Errors
```bash
# Error: "No such container: pdf2htmlex-service"
# Check actual container name
docker ps --filter "name=pdf2htmlex-service" --format "table {{.Names}}"

# Verify container is accessible
docker exec dynamic-web-plugins-pdf2htmlex-service-1 echo "test"

# Check service discovery in web container
docker exec web docker ps --filter "name=pdf2htmlex-service" --format "{{.Names}}"
```

### Conversion Failures
```bash
# Check shared volume permissions
ls -la /app/shared/

# Verify container can access shared volume
docker exec pdf2htmlex-service ls -la /shared/

# Test pdf2htmlEX directly
docker exec pdf2htmlex-service pdf2htmlEX --help
```

### Permission Issues
```bash
# Fix shared directory permissions
sudo chown -R $(id -u):$(id -g) /app/shared/

# Check Docker socket permissions
ls -la /var/run/docker.sock

# Restart services
docker compose restart
```

## 📋 Configuration Options

- **Zoom Level**: Adjust rendering quality (default: 1.3)
- **Embed CSS**: Include CSS styles in HTML (default: true)
- **Embed JavaScript**: Include JavaScript in HTML (default: true)  
- **Embed Images**: Include images as base64 data (default: true)
- **Output Filename**: Custom filename for converted HTML

## 🔗 API Usage

```bash
# Convert PDF via API
curl -X POST http://localhost:8000/api/plugin/pdf2html/execute \
  -F "input_file=@document.pdf" \
  -F "zoom=1.5" \
  -F "embed_css=true" \
  -F "embed_javascript=true" \
  -F "embed_images=true"
```

## 🛡️ Security Considerations

- **Isolated Execution**: pdf2htmlEX runs in separate container
- **Docker Socket Access**: Main app has Docker daemon access for container communication
- **Controlled Environment**: Commands executed only in designated service containers
- **Resource Limits**: Container-based resource management
- **⚠️ Security Note**: Docker socket access provides elevated privileges - monitor in production

## 🔄 Scaling

To handle higher loads:

```yaml
# In docker-compose.yml
pdf2htmlex-service:
  # ... existing config
  deploy:
    replicas: 3  # Multiple instances
    resources:
      limits:
        cpus: "1.0"
        memory: 1G
```

## 📝 Development

For development, you can run pdf2htmlEX directly:

```bash
# Enter the service container
docker exec -it pdf2htmlex-service /bin/bash

# Test conversions manually
pdf2htmlEX --zoom 1.3 --embed-css=1 /shared/test.pdf
``` 