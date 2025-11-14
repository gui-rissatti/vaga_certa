#!/bin/bash

# Script de deploy para produção
# Executa checklist completo e deploy seguro

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Deploy para Produção${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

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
echo "Branch: $(git branch --show-current 2>/dev/null || echo "no-branch")"
echo ""

# Função para confirmar
confirm() {
    local message=$1
    read -p "$message (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deploy cancelado${NC}"
        exit 0
    fi
}

# Checklist pré-deploy
echo -e "${BLUE}Checklist Pré-Deploy:${NC}"
echo ""

# 1. Verificar branch
echo -n "1. Branch é main/master? "
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}   Deploy para produção deve ser feito a partir da branch main/master${NC}"
    exit 1
fi

# 2. Verificar mudanças não commitadas
echo -n "2. Working tree limpo? "
if git diff-index --quiet HEAD --; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}   Existem mudanças não commitadas${NC}"
    exit 1
fi

# 3. Verificar variáveis de ambiente
echo -n "3. Variáveis de ambiente configuradas? "
if ./scripts/deploy/check-env.sh > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo ""
    ./scripts/deploy/check-env.sh
    exit 1
fi

# 4. Verificar testes (opcional se CI/CD passou)
if [ "$SKIP_TESTS" != "true" ]; then
    echo -n "4. Executar testes? "
    confirm ""
    
    cd backend
    pytest ../tests/backend/unit/ -v --tb=short || {
        echo -e "${RED}✗ Testes falharam${NC}"
        exit 1
    }
    cd ..
    echo -e "${GREEN}   ✓ Testes passaram${NC}"
else
    echo "4. Testes: PULADOS (SKIP_TESTS=true)"
fi

# 5. Build
echo "5. Executando builds..."
./scripts/deploy/build-backend.sh > /dev/null 2>&1 && echo -e "   Backend: ${GREEN}✓${NC}"
./scripts/deploy/build-frontend.sh > /dev/null 2>&1 && echo -e "   Frontend: ${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}✓ Checklist pré-deploy concluído${NC}"
echo ""

# Confirmação final
echo -e "${YELLOW}⚠ ATENÇÃO: Deploy para PRODUÇÃO${NC}"
echo ""
confirm "Confirmar deploy?"

# Deploy Backend (Render)
echo ""
echo -e "${BLUE}Deploying Backend...${NC}"
if [ -n "$RENDER_API_KEY" ] && [ -n "$RENDER_SERVICE_ID_PRODUCTION" ]; then
    curl -X POST \
        "https://api.render.com/v1/services/$RENDER_SERVICE_ID_PRODUCTION/deploys" \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"clearCache": false}' \
        2>/dev/null && echo -e "${GREEN}✓ Deploy iniciado${NC}" || echo -e "${YELLOW}⚠ Erro ao iniciar deploy${NC}"
else
    echo -e "${YELLOW}⚠ Render API não configurada - deploy manual necessário${NC}"
fi

# Deploy Frontend (Vercel)
echo ""
echo -e "${BLUE}Deploying Frontend...${NC}"
if [ -n "$VERCEL_TOKEN" ]; then
    cd frontend
    vercel --prod --token=$VERCEL_TOKEN 2>/dev/null && \
        echo -e "${GREEN}✓ Deploy concluído${NC}" || \
        echo -e "${YELLOW}⚠ Erro no deploy${NC}"
    cd ..
else
    echo -e "${YELLOW}⚠ Vercel token não configurado - deploy manual necessário${NC}"
fi

# Aguarda deploy
echo ""
echo "Aguardando deploys (60s)..."
sleep 60

# Health check
echo ""
echo -e "${BLUE}Executando health check...${NC}"
export BACKEND_URL=${PRODUCTION_BACKEND_URL:-"https://api-vaga-certa.onrender.com"}
export FRONTEND_URL=${PRODUCTION_FRONTEND_URL:-"https://vaga-certa.vercel.app"}

if ./scripts/deploy/health-check.sh; then
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${GREEN}✓ Deploy concluído com sucesso!${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "URLs:"
    echo "  Backend:  $BACKEND_URL"
    echo "  Frontend: $FRONTEND_URL"
    echo ""
    echo "Próximos passos:"
    echo "  1. Monitorar logs por 10-15 minutos"
    echo "  2. Testar funcionalidade principal"
    echo "  3. Verificar métricas de performance"
    echo ""
else
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${RED}✗ Health check falhou após deploy${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "Ações recomendadas:"
    echo "  1. Verificar logs dos serviços"
    echo "  2. Considerar rollback: ./scripts/deploy/rollback.sh all"
    echo ""
    exit 1
fi

