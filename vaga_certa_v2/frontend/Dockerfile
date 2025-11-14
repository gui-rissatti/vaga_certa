# Multi-stage build para frontend React/Vite

# Build stage: compila aplicação
FROM node:20-alpine AS builder

WORKDIR /app

# Copia package files primeiro (cache layer)
COPY package*.json ./

# Instala dependências (incluindo devDependencies para build)
RUN npm ci --ignore-scripts

# Copia código fonte
COPY . .

# Build da aplicação com Vite
RUN npm run build

# Runtime stage: serve com nginx
FROM nginx:1.27-alpine

# Remove configuração padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/

# Copia build do estágio anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Cria usuário não-root
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

# Expõe porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Muda para usuário não-root
USER appuser

# Inicia nginx
CMD ["nginx", "-g", "daemon off;"]

