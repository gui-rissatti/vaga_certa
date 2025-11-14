# Scripts de Deploy - Vaga Certa v2

Scripts automatizados para build, deploy, rollback e manutenção da aplicação.

## Estrutura

```
scripts/
└── deploy/
    ├── check-env.sh           # Validação de variáveis de ambiente
    ├── build-backend.sh       # Build da imagem Docker backend
    ├── build-frontend.sh      # Build da aplicação React
    ├── health-check.sh        # Verificação de saúde dos serviços
    ├── rollback.sh            # Rollback para versão anterior
    └── deploy-production.sh   # Deploy completo para produção
```

## Pré-requisitos

- **Linux/Mac:** Bash 4.0+
- **Windows:** Git Bash ou WSL2
- **Dependências:**
  - `curl` - Requisições HTTP
  - `jq` - Parsing JSON (opcional)
  - `docker` - Para builds locais
  - `git` - Versionamento
  - `bc` - Cálculos (para response time)

## Scripts Disponíveis

### 1. check-env.sh

Valida se todas as variáveis de ambiente obrigatórias estão configuradas.

**Uso:**
```bash
./scripts/deploy/check-env.sh
```

**Variáveis validadas:**
- `GOOGLE_API_KEY` (obrigatória)
- `VITE_API_URL` (obrigatória)
- `LANGCHAIN_API_KEY` (opcional)
- `RENDER_API_KEY` (para CI/CD)
- `VERCEL_TOKEN` (para CI/CD)

**Saída:**
- ✓ Verde: Variável configurada corretamente
- ✗ Vermelho: Variável faltando ou inválida
- ⚠ Amarelo: Variável opcional não configurada

### 2. build-backend.sh

Constrói a imagem Docker do backend com versionamento automático.

**Uso:**
```bash
./scripts/deploy/build-backend.sh
```

**O que faz:**
- Detecta versão (tag Git ou commit hash)
- Builda imagem Docker multi-stage
- Cria tags `latest` e `$VERSION`
- Executa teste básico de importação
- Mostra tamanho da imagem

**Saída:**
- Imagem: `vaga-certa-backend:latest`
- Imagem: `vaga-certa-backend:<version>`

### 3. build-frontend.sh

Compila a aplicação React com Vite para produção.

**Uso:**
```bash
./scripts/deploy/build-frontend.sh
```

**O que faz:**
- Detecta versão
- Instala dependências (se necessário)
- Executa `npm run build`
- Mostra tamanho do build
- Lista arquivos principais gerados

**Saída:**
- Build em: `frontend/dist/`

### 4. health-check.sh

Verifica se os serviços estão saudáveis e responsivos.

**Uso:**
```bash
# Local (padrão)
./scripts/deploy/health-check.sh

# Produção
BACKEND_URL=https://api.example.com \
FRONTEND_URL=https://example.com \
./scripts/deploy/health-check.sh
```

**O que faz:**
- Testa endpoint `/health` do backend
- Testa carregamento do frontend
- Mede tempo de resposta
- Mostra detalhes do health (se disponível)
- Alerta se tempo > 2s

**Exit codes:**
- `0`: Todos os serviços saudáveis
- `1`: Um ou mais serviços com problema

### 5. rollback.sh

Reverte deploy para versão anterior em caso de problema.

**Uso:**
```bash
# Rollback completo
./scripts/deploy/rollback.sh all

# Apenas backend
./scripts/deploy/rollback.sh backend

# Apenas frontend
./scripts/deploy/rollback.sh frontend

# Para versão específica
./scripts/deploy/rollback.sh frontend v1.2.0
```

**O que faz:**
- Lista últimos deployments
- Solicita confirmação
- Executa rollback via API (Render/Vercel)
- Executa health check após rollback

**Requisitos:**
- `RENDER_API_KEY` (para backend)
- `VERCEL_TOKEN` (para frontend)

### 6. deploy-production.sh

Script completo de deploy para produção com checklist de segurança.

**Uso:**
```bash
# Deploy completo
./scripts/deploy/deploy-production.sh

# Pular testes (não recomendado)
SKIP_TESTS=true ./scripts/deploy/deploy-production.sh
```

**Checklist pré-deploy:**
1. ✓ Verifica se está na branch `main/master`
2. ✓ Verifica se working tree está limpo
3. ✓ Valida variáveis de ambiente
4. ✓ Executa testes unitários
5. ✓ Executa builds (backend + frontend)
6. ⚠ Solicita confirmação final

**O que faz:**
- Executa checklist completo
- Deploy backend (Render API)
- Deploy frontend (Vercel CLI)
- Aguarda 60s (warm-up)
- Executa health check
- Mostra URLs de produção

**Exit codes:**
- `0`: Deploy concluído com sucesso
- `1`: Deploy falhou (checklist ou health check)

**Variáveis de ambiente:**
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID_PRODUCTION`
- `VERCEL_TOKEN`
- `PRODUCTION_BACKEND_URL`
- `PRODUCTION_FRONTEND_URL`

## Workflows Típicos

### Deploy Local (Docker)

```bash
# 1. Valida ambiente
./scripts/deploy/check-env.sh

# 2. Build
./scripts/deploy/build-backend.sh
./scripts/deploy/build-frontend.sh

# 3. Sobe containers
docker-compose up -d

# 4. Verifica saúde
./scripts/deploy/health-check.sh
```

### Deploy Produção

```bash
# 1. Certifique-se de estar em main
git checkout main
git pull origin main

# 2. Execute deploy
./scripts/deploy/deploy-production.sh

# 3. Monitore logs
# (verificar dashboards Render/Vercel)
```

### Rollback de Emergência

```bash
# 1. Identifica problema
./scripts/deploy/health-check.sh  # Falhou

# 2. Rollback imediato
./scripts/deploy/rollback.sh all

# 3. Verifica estabilidade
./scripts/deploy/health-check.sh

# 4. Investiga causa
# (verificar logs, criar issue)
```

## Troubleshooting

### Permission Denied

```bash
chmod +x scripts/deploy/*.sh
```

### Scripts não rodam no Windows

Use Git Bash ou WSL2:
```bash
# Git Bash
"C:\Program Files\Git\bin\bash.exe" scripts/deploy/check-env.sh

# WSL2
wsl ./scripts/deploy/check-env.sh
```

### Comando não encontrado

Instale dependências:
```bash
# Ubuntu/Debian
sudo apt install curl jq bc

# macOS
brew install curl jq bc
```

### Health check falha localmente

Verifique se os serviços estão rodando:
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Logs Docker
docker-compose logs -f
```

### Rollback não funciona

Fallback manual:
- **Render:** Dashboard > Deploy > Rollback to Previous
- **Vercel:** Dashboard > Deployments > Promote to Production

## Boas Práticas

1. **Sempre execute `check-env.sh` antes de deploy**
2. **Teste localmente com Docker antes de produção**
3. **Monitore logs por 10-15min após deploy**
4. **Mantenha backup de configurações (.env)**
5. **Documente problemas encontrados em issues**
6. **Use tags Git para versões de produção**

## Referências

- [DEPLOY_GUIDE.md](../../DEPLOY_GUIDE.md) - Guia completo de deploy
- [README.md](../../README.md) - Documentação principal
- [DevOps-Guide](https://github.com/Tikam02/DevOps-Guide) - Referência de boas práticas

