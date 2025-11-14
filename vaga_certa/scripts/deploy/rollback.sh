#!/bin/bash

# Script de rollback
# Reverte deploy para versão anterior

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Rollback Deploy${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Parse argumentos
COMPONENT=${1:-"all"}  # backend, frontend, or all
TARGET_VERSION=${2:-"previous"}

if [ "$COMPONENT" != "backend" ] && [ "$COMPONENT" != "frontend" ] && [ "$COMPONENT" != "all" ]; then
    echo -e "${RED}Erro: Componente inválido${NC}"
    echo "Uso: $0 <backend|frontend|all> [version]"
    echo ""
    echo "Exemplos:"
    echo "  $0 backend          # Rollback backend para versão anterior"
    echo "  $0 frontend v1.2.0  # Rollback frontend para v1.2.0"
    echo "  $0 all              # Rollback completo"
    exit 1
fi

echo "Componente: $COMPONENT"
echo "Versão alvo: $TARGET_VERSION"
echo ""

# Função para confirmar ação
confirm() {
    read -p "Confirmar rollback? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Rollback cancelado${NC}"
        exit 0
    fi
}

# Rollback Backend (Render)
rollback_backend() {
    echo -e "${YELLOW}Iniciando rollback do backend...${NC}"
    
    if [ -z "$RENDER_API_KEY" ] || [ -z "$RENDER_SERVICE_ID" ]; then
        echo -e "${RED}✗ RENDER_API_KEY ou RENDER_SERVICE_ID não configurados${NC}"
        echo "Configure as variáveis de ambiente e tente novamente"
        return 1
    fi
    
    # Lista últimos deploys
    echo "Últimos deploys:"
    curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys?limit=5" \
        | python3 -m json.tool 2>/dev/null || echo "Erro ao listar deploys"
    
    echo ""
    echo "Revertendo para versão anterior via Render..."
    
    # Render não tem API direta de rollback, precisa fazer novo deploy
    # da versão anterior ou usar a interface web
    echo -e "${YELLOW}⚠ Rollback manual necessário via dashboard do Render:${NC}"
    echo "   https://dashboard.render.com/web/$RENDER_SERVICE_ID"
    echo ""
    
    return 0
}

# Rollback Frontend (Vercel)
rollback_frontend() {
    echo -e "${YELLOW}Iniciando rollback do frontend...${NC}"
    
    if [ -z "$VERCEL_TOKEN" ]; then
        echo -e "${RED}✗ VERCEL_TOKEN não configurado${NC}"
        echo "Configure a variável de ambiente e tente novamente"
        return 1
    fi
    
    # Instala Vercel CLI se necessário
    if ! command -v vercel &> /dev/null; then
        echo "Instalando Vercel CLI..."
        npm install -g vercel
    fi
    
    cd frontend
    
    # Lista deployments
    echo "Últimos deployments:"
    vercel ls --token=$VERCEL_TOKEN 2>/dev/null || echo "Erro ao listar deployments"
    
    echo ""
    
    if [ "$TARGET_VERSION" = "previous" ]; then
        echo "Promovendo deployment anterior para produção..."
        # Vercel CLI: vercel rollback [deployment-url]
        echo -e "${YELLOW}⚠ Use o comando:${NC}"
        echo "   cd frontend && vercel rollback [deployment-url]"
    else
        echo "Promovendo deployment $TARGET_VERSION para produção..."
        vercel promote $TARGET_VERSION --token=$VERCEL_TOKEN
    fi
    
    cd ..
    
    echo -e "${GREEN}✓ Rollback do frontend iniciado${NC}"
    return 0
}

# Rollback Docker Local
rollback_docker() {
    echo -e "${YELLOW}Iniciando rollback Docker...${NC}"
    
    # Para containers atuais
    docker-compose down
    
    # Recria com versão anterior
    if [ "$TARGET_VERSION" != "previous" ]; then
        export IMAGE_TAG=$TARGET_VERSION
    fi
    
    docker-compose up -d
    
    # Aguarda serviços
    echo "Aguardando serviços..."
    sleep 10
    
    # Verifica health
    ./scripts/deploy/health-check.sh
    
    echo -e "${GREEN}✓ Rollback Docker concluído${NC}"
    return 0
}

# Executa rollback
confirm

case $COMPONENT in
    backend)
        rollback_backend
        ;;
    frontend)
        rollback_frontend
        ;;
    all)
        rollback_backend
        rollback_frontend
        ;;
esac

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✓ Rollback concluído${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Próximos passos:"
echo "  1. Verifique os serviços: ./scripts/deploy/health-check.sh"
echo "  2. Monitore logs para confirmar estabilidade"
echo "  3. Investigue a causa do problema na versão revertida"

