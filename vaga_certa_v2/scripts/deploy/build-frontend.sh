#!/bin/bash

# Script de build do frontend
# Constrói a aplicação React com Vite

set -e  # Exit on error

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Build Frontend${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd frontend

# Determina versão
if git describe --tags --exact-match 2>/dev/null; then
    VERSION=$(git describe --tags --exact-match)
elif git rev-parse --short HEAD 2>/dev/null; then
    VERSION=$(git rev-parse --short HEAD)
else
    # Fallback se não houver commits
    VERSION="2.0.0-dev"
fi

echo "Versão: $VERSION"
echo "Iniciando build..."
echo ""

# Instala dependências (se necessário)
if [ ! -d "node_modules" ]; then
    echo "Instalando dependências..."
    npm ci
    echo ""
fi

# Build
npm run build

echo ""
echo -e "${GREEN}✓ Build concluído com sucesso${NC}"
echo ""

# Informações do build
echo "Arquivos gerados em: frontend/dist"
echo "Tamanho do build:"
du -sh dist
echo ""
echo "Arquivos principais:"
ls -lh dist/assets/*.js dist/assets/*.css 2>/dev/null || true

echo ""
echo -e "${BLUE}=========================================${NC}"

