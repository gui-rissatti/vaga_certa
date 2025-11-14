#!/bin/bash

# Script de health check
# Verifica se os serviços estão saudáveis após deploy

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Health Check${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# URLs padrão (podem ser sobrescritos por variáveis de ambiente)
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}

# Timeout para requests
TIMEOUT=10
MAX_RETRIES=5

# Função para verificar endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local retries=0
    
    echo -n "Verificando $name... "
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s -m $TIMEOUT "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            echo -n "."
            sleep 2
        fi
    done
    
    echo -e "${RED}✗ FALHOU${NC}"
    return 1
}

# Função para verificar health detalhado
check_health_detailed() {
    local url=$1
    local name=$2
    
    echo ""
    echo "$name Health Details:"
    echo "---"
    
    response=$(curl -s -m $TIMEOUT "$url")
    
    if [ $? -eq 0 ]; then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        echo ""
        return 0
    else
        echo -e "${RED}Falha ao obter detalhes${NC}"
        echo ""
        return 1
    fi
}

# Função para verificar tempo de resposta
check_response_time() {
    local url=$1
    local name=$2
    
    echo -n "Tempo de resposta $name: "
    
    time_total=$(curl -s -o /dev/null -w "%{time_total}" -m $TIMEOUT "$url" 2>/dev/null || echo "N/A")
    
    if [ "$time_total" != "N/A" ]; then
        time_ms=$(echo "$time_total * 1000" | bc)
        echo -e "${GREEN}${time_ms}ms${NC}"
        
        # Alerta se muito lento
        if (( $(echo "$time_total > 2.0" | bc -l) )); then
            echo -e "${YELLOW}⚠ Aviso: Tempo de resposta alto (> 2s)${NC}"
        fi
    else
        echo -e "${RED}N/A${NC}"
    fi
}

errors=0

# Check Backend
echo "Backend:"
check_endpoint "$BACKEND_URL/health" "Backend Health" || ((errors++))
check_response_time "$BACKEND_URL/health" "Backend"
check_health_detailed "$BACKEND_URL/health" "Backend" || true
echo ""

# Check Frontend
echo "Frontend:"
check_endpoint "$FRONTEND_URL" "Frontend" || ((errors++))
check_response_time "$FRONTEND_URL" "Frontend"
echo ""

# Resumo
echo -e "${BLUE}=========================================${NC}"
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓ Todos os serviços estão saudáveis${NC}"
    echo -e "${BLUE}=========================================${NC}"
    exit 0
else
    echo -e "${RED}✗ $errors serviço(s) com problema${NC}"
    echo -e "${BLUE}=========================================${NC}"
    exit 1
fi

