#!/bin/bash

# Script de validação de variáveis de ambiente
# Verifica se todas as variáveis obrigatórias estão configuradas

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Carrega variáveis do arquivo .env do backend
if [ -f "backend/.env" ]; then
    # Remove BOM, comentários e linhas vazias, depois exporta
    set -a
    source <(grep -E '^[A-Z_]+=.*' backend/.env | sed 's/\r$//')
    set +a
fi

# Carrega variáveis do arquivo .env do frontend  
if [ -f "frontend/.env" ]; then
    set -a
    source <(grep -E '^[A-Z_]+=.*' frontend/.env | sed 's/\r$//')
    set +a
fi

echo "========================================="
echo "Validando Variáveis de Ambiente"
echo "========================================="
echo ""

# Função para verificar variável
check_var() {
    local var_name=$1
    local var_value=${!var_name}
    local is_required=$2
    local is_secret=$3
    
    if [ -z "$var_value" ]; then
        if [ "$is_required" = "true" ]; then
            echo -e "${RED}✗${NC} $var_name: ${RED}NÃO CONFIGURADA (obrigatória)${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠${NC} $var_name: ${YELLOW}não configurada (opcional)${NC}"
            return 0
        fi
    else
        # Verifica se não é placeholder
        if [[ "$var_value" == *"your_"* ]] || [[ "$var_value" == *"example"* ]]; then
            echo -e "${RED}✗${NC} $var_name: ${RED}contém placeholder, configure valor real${NC}"
            return 1
        fi
        
        if [ "$is_secret" = "true" ]; then
            echo -e "${GREEN}✓${NC} $var_name: ${GREEN}configurada${NC} (valor oculto)"
        else
            echo -e "${GREEN}✓${NC} $var_name: ${GREEN}$var_value${NC}"
        fi
        return 0
    fi
}

errors=0

# Variáveis Backend Obrigatórias
echo "Backend (Obrigatórias):"
check_var "GOOGLE_API_KEY" "true" "true" || ((errors++))
echo ""

# Variáveis Backend Opcionais
echo "Backend (Opcionais):"
check_var "LANGCHAIN_API_KEY" "false" "true"
check_var "LANGCHAIN_TRACING_V2" "false" "false"
check_var "ENVIRONMENT" "false" "false"
check_var "LOG_LEVEL" "false" "false"
echo ""

# Variáveis Frontend
echo "Frontend:"
check_var "VITE_API_URL" "true" "false" || ((errors++))
echo ""

# Variáveis CI/CD (se aplicável)
if [ -n "$CI" ]; then
    echo "CI/CD:"
    check_var "RENDER_API_KEY" "false" "true"
    check_var "VERCEL_TOKEN" "false" "true"
    echo ""
fi

# Resumo
echo "========================================="
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓ Todas as variáveis obrigatórias estão configuradas${NC}"
    echo "========================================="
    exit 0
else
    echo -e "${RED}✗ $errors variável(is) obrigatória(s) faltando${NC}"
    echo "========================================="
    echo ""
    echo "Como configurar:"
    echo "  Backend: copie backend/.env.example para backend/.env"
    echo "  Frontend: copie frontend/.env.example para frontend/.env"
    echo "  Configure os valores reais em cada arquivo .env"
    exit 1
fi

