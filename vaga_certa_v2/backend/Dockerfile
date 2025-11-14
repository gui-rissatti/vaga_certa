# Multi-stage build para otimizar tamanho da imagem final
# Build stage: instala dependências
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas requirements primeiro (cache layer)
COPY requirements.txt .

# Instala dependências Python em diretório isolado
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage: imagem final enxuta
FROM python:3.11-slim

WORKDIR /app

# Instala apenas dependências de runtime necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copia dependências instaladas do builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Adiciona binários Python ao PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copia código da aplicação
COPY --chown=appuser:appuser . .

# Muda para usuário não-root
USER appuser

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização (produção com Gunicorn)
CMD ["gunicorn", "api.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "300", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

