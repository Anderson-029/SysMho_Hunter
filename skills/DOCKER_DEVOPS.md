# Skill: Docker & DevOps — Infraestructura Profesional

Eres experto en containerización y orquestación para proyectos de seguridad. Sabes construir entornos reproducibles, seguros y portables.

## Docker Compose para SysMho Hunter

### Estructura de Servicios
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sysmho_hunter
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database:/docker-entrypoint-initdb.d  # auto-load SQL scripts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      retries: 5

  backend:
    build: .
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
    env_file: .env
    volumes:
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

## Dockerfile Backend (Optimizado)
```dockerfile
FROM python:3.12-slim

# Instalar herramientas de seguridad del sistema
RUN apt-get update && apt-get install -y \
    nmap ffuf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python (cacheado por capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Principios de Seguridad en Docker
1. **Nunca** usar `root` dentro del container — crear usuario no privilegiado
2. **Nunca** hardcodear secretos en Dockerfile o docker-compose.yml
3. Usar `.dockerignore` para excluir `.env`, `venv/`, `*.log`
4. Escanear imagen con `docker scout` o `trivy` antes de usar

## Variables de Entorno — Gestión Segura
```bash
# .env (nunca commiteado)
GEMINI_API_KEY=real_key_here
DB_PASSWORD=strong_random_password

# .env.example (commiteado, sin valores reales)
GEMINI_API_KEY=your_gemini_api_key
DB_PASSWORD=change_me_in_production
```

## Comandos de Desarrollo
```bash
docker compose up -d db          # Solo levantar BD
docker compose up --build        # Rebuild y levantar todo
docker compose logs -f backend   # Ver logs en tiempo real
docker compose exec backend bash # Entrar al container
docker compose down -v           # Bajar y limpiar volúmenes
```
