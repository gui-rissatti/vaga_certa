#!/bin/bash

# Script de build do backend
# Constrói a imagem Docker do backend e aplica tag com versão

set -e  # Exit on error

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Build Backend Docker Image${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Determina versão (usa tag git ou commit hash)
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

# Build da imagem
cd backend

docker build \
    --tag vaga-certa-backend:latest \
    --tag vaga-certa-backend:$VERSION \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "no-vcs") \
    --build-arg VERSION=$VERSION \
    .

echo ""
echo -e "${GREEN}✓ Build concluído com sucesso${NC}"
echo ""
echo "Imagens criadas:"
echo "  - vaga-certa-backend:latest"
echo "  - vaga-certa-backend:$VERSION"
echo ""

# Informações da imagem
echo "Tamanho da imagem:"
docker images vaga-certa-backend:latest --format "{{.Size}}"
echo ""

# Teste básico
echo "Testando imagem..."
docker run --rm \
    -e GOOGLE_API_KEY=test-key \
    -e LANGCHAIN_TRACING_V2=false \
    vaga-certa-backend:latest \
    python -c "import api.main; print('✓ Importação OK')"

echo ""
echo -e "${GREEN}✓ Imagem testada com sucesso${NC}"
echo -e "${BLUE}=========================================${NC}"

