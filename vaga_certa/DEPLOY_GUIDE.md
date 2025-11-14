# Guia de Deploy - Vaga Certa v2

Guia completo para deploy, manutenção e troubleshooting do MVP em ambientes de produção.

**Público-alvo:** Engenheiros DevOps, Desenvolvedores, SREs

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Setup Inicial](#setup-inicial)
3. [Deploy Manual](#deploy-manual)
4. [Deploy Automatizado (CI/CD)](#deploy-automatizado-cicd)
5. [Gerenciamento de Secrets](#gerenciamento-de-secrets)
6. [Monitoramento](#monitoramento)
7. [Rollback](#rollback)
8. [Troubleshooting](#troubleshooting)
9. [Referências](#referências)

---

## Pré-requisitos

### Contas e Acessos

- **GitHub Account:** Para repositório e CI/CD
- **Render Account:** Para backend ([render.com](https://render.com))
- **Vercel Account:** Para frontend ([vercel.com](https://vercel.com))
- **Google Cloud Console:** Para Gemini API ([aistudio.google.com](https://aistudio.google.com/app/apikey))
- **LangSmith** (opcional): Para observabilidade ([smith.langchain.com](https://smith.langchain.com))

### Ferramentas Locais

- **Git** 2.30+
- **Docker** 20.10+ e Docker Compose 2.0+
- **Python** 3.11+
- **Node.js** 20+
- **Bash** 4.0+ (Git Bash no Windows ou WSL2)

### APIs e Tokens

| Service | Token/Key | Onde Obter | Obrigatório |
|---------|-----------|------------|-------------|
| Google Gemini | `GOOGLE_API_KEY` | [AI Studio](https://aistudio.google.com/app/apikey) | ✓ Sim |
| Render | `RENDER_API_KEY` | Dashboard > Account Settings > API Keys | Para CI/CD |
| Vercel | `VERCEL_TOKEN` | Settings > Tokens | Para CI/CD |
| LangSmith | `LANGCHAIN_API_KEY` | [Settings](https://smith.langchain.com/settings) | Opcional |

---

## Setup Inicial

### 1. Clone do Repositório

```bash
git clone https://github.com/seu-usuario/vaga_certa_v2.git
cd vaga_certa_v2
```

### 2. Configuração de Variáveis de Ambiente

#### Backend

```bash
cd backend
cp .env.example .env
```

Edite `backend/.env`:

```bash
# Obrigatório
GOOGLE_API_KEY=sua_chave_real_aqui

# Opcional - LangSmith
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false

# Configurações
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### Frontend

```bash
cd ../frontend
cp .env.example .env
```

Edite `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
```

### 3. Validação de Ambiente

```bash
cd ..
./scripts/deploy/check-env.sh
```

Saída esperada: ✓ Todas as variáveis obrigatórias estão configuradas

---

## Deploy Manual

### Opção 1: Docker Local

**Passo 1:** Build das imagens

```bash
./scripts/deploy/build-backend.sh
docker-compose build
```

**Passo 2:** Inicie os serviços

```bash
docker-compose up -d
```

**Passo 3:** Verifique saúde

```bash
./scripts/deploy/health-check.sh
```

**Passo 4:** Acesse a aplicação

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

**Logs:**

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas frontend
docker-compose logs -f frontend
```

**Parar serviços:**

```bash
docker-compose down
```

### Opção 2: Deploy Render + Vercel

#### Backend (Render)

**Passo 1:** Crie conta em [render.com](https://render.com)

**Passo 2:** New Web Service

- **Repository:** Conecte seu repositório GitHub
- **Branch:** `main`
- **Root Directory:** `backend`
- **Environment:** `Python 3`
- **Build Command:**
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  gunicorn api.main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 300 --log-level info
  ```

**Passo 3:** Configure Environment Variables

```
GOOGLE_API_KEY=sua_chave_aqui
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://vaga-certa.vercel.app
```

**Passo 4:** Configure Health Check

- **Path:** `/health`
- **Interval:** 30s
- **Timeout:** 10s

**Passo 5:** Deploy

- Click em "Create Web Service"
- Aguarde build (5-10min)
- Verifique logs para erros
- Teste health: `https://seu-app.onrender.com/health`

#### Frontend (Vercel)

**Passo 1:** Crie conta em [vercel.com](https://vercel.com)

**Passo 2:** Import Project

- **Repository:** Conecte GitHub
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

**Passo 3:** Configure Environment Variables

```
VITE_API_URL=https://seu-backend.onrender.com
```

**Passo 4:** Deploy

- Click em "Deploy"
- Aguarde build (2-3min)
- Teste: `https://seu-app.vercel.app`

---

## Deploy Automatizado (CI/CD)

### GitHub Actions

O repositório inclui 3 workflows automatizados:

1. **backend-ci.yml:** Lint, test, build e deploy backend
2. **frontend-ci.yml:** Lint, build e deploy frontend
3. **smoke-test.yml:** Testes pós-deploy

### Configuração de Secrets

No GitHub, vá em **Settings > Secrets and variables > Actions** e adicione:

#### Secrets Obrigatórios

| Secret | Valor | Uso |
|--------|-------|-----|
| `GOOGLE_API_KEY` | Chave real Gemini | Backend prod |
| `GOOGLE_API_KEY_TEST` | Chave teste ou mock | CI tests |
| `RENDER_API_KEY` | Token Render | Deploy backend |
| `RENDER_SERVICE_ID_PRODUCTION` | ID serviço prod | Deploy prod |
| `VERCEL_TOKEN` | Token Vercel | Deploy frontend |
| `VERCEL_ORG_ID` | ID organização | Deploy |
| `VERCEL_PROJECT_ID` | ID projeto | Deploy |

#### Secrets Opcionais

| Secret | Valor | Uso |
|--------|-------|-----|
| `RENDER_SERVICE_ID_STAGING` | ID serviço staging | Deploy staging |
| `LANGCHAIN_API_KEY` | Token LangSmith | Observabilidade |
| `PRODUCTION_BACKEND_URL` | URL backend prod | Smoke tests |
| `PRODUCTION_FRONTEND_URL` | URL frontend prod | Smoke tests |

### Workflow de Deploy

#### Deploy Staging (Branch `develop`)

```bash
git checkout develop
git add .
git commit -m "feat: nova funcionalidade"
git push origin develop
```

GitHub Actions automaticamente:
1. Executa lint e testes
2. Builda imagens Docker
3. Deploy para staging
4. Executa smoke tests

#### Deploy Production (Branch `main`)

```bash
git checkout main
git merge develop
git push origin main
```

GitHub Actions automaticamente:
1. Executa pipeline completo
2. Deploy para produção
3. Aguarda 60s (warm-up)
4. Executa smoke tests
5. Notifica sucesso/falha

**Aprovação Manual:**

Para adicionar aprovação manual antes de produção:

1. GitHub > Settings > Environments
2. Crie environment `production`
3. Enable "Required reviewers"
4. Adicione revisores

### Deploy Manual via Script

Para deploy direto via script (sem CI/CD):

```bash
# Validar ambiente primeiro
./scripts/deploy/check-env.sh

# Deploy completo
./scripts/deploy/deploy-production.sh

# Ou pular testes (não recomendado)
SKIP_TESTS=true ./scripts/deploy/deploy-production.sh
```

---

## Gerenciamento de Secrets

### Rotação de API Keys

#### Google Gemini API Key

**Quando rotacionar:**
- Suspeita de comprometimento
- A cada 90 dias (boa prática)
- Após remoção de membro da equipe

**Passo-a-passo:**

1. **Gere nova chave:**
   - Acesse [AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Create API Key"
   - Copie nova chave

2. **Atualize em Render:**
   - Dashboard > Service > Environment
   - Edit `GOOGLE_API_KEY`
   - Salvar e redeploy

3. **Atualize no GitHub:**
   - Settings > Secrets > Edit `GOOGLE_API_KEY`
   - Cole nova chave
   - Save

4. **Revogue chave antiga:**
   - AI Studio > API Keys
   - Delete chave antiga

5. **Valide:**
   ```bash
   curl https://seu-backend.onrender.com/health
   ```

#### Render API Key

1. Render Dashboard > Account Settings > API Keys
2. Revoke old key
3. Create new key
4. Update GitHub secret `RENDER_API_KEY`

#### Vercel Token

1. Vercel > Settings > Tokens
2. Delete old token
3. Create new token
4. Update GitHub secret `VERCEL_TOKEN`

### Backup de Configurações

```bash
# Salve .env em local seguro (1Password, Vault, etc)
cp backend/.env backend/.env.backup
cp frontend/.env frontend/.env.backup

# NUNCA commite .env no Git!
```

---

## Monitoramento

### Health Checks

#### Backend

**Endpoint:** `GET /health`

**Resposta esperada (200 OK):**

```json
{
  "status": "healthy",
  "environment": "production",
  "version": "2.0.0",
  "config": {
    "google_api_configured": true,
    "langsmith_enabled": false,
    "agents_initialized": true
  }
}
```

**Monitoramento automático:**
- Render: Dashboard > Service > Events (auto)
- Custom: Pingdom, UptimeRobot, etc

#### Frontend

**Endpoint:** `GET /`

**Resposta esperada:** HTML (200 OK)

**Monitoramento:**
- Vercel Analytics (automático)
- Custom: Google Analytics, Sentry

### Logs

#### Backend (Render)

**Acesso:**
- Dashboard > Service > Logs
- Logs estruturados JSON (structlog)

**Filtros úteis:**
```
level:"ERROR"
level:"WARNING"
"status_code":500
"endpoint":"/generate-complete"
```

**Download logs:**
```bash
# Via API
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$RENDER_SERVICE_ID/logs?limit=1000"
```

#### Frontend (Vercel)

**Acesso:**
- Dashboard > Deployment > Function Logs
- Real-time logs (últimas 1000 requests)

**Runtime Logs:**
- Browser DevTools > Console
- Erros capturados por `window.onerror`

### Métricas

#### Backend

**Render Metrics (Dashboard):**
- CPU usage
- Memory usage
- HTTP status codes
- Response time (p50, p95, p99)
- Requests/minute

**Alertas recomendados:**
- CPU > 80% por 5min
- Memory > 90% por 5min
- Error rate > 5%
- P95 response time > 5s

#### Frontend

**Vercel Analytics:**
- Core Web Vitals (LCP, FID, CLS)
- Page views
- Unique visitors
- Deployment frequency

**Custom Metrics:**
- Tempo de geração de CV
- Taxa de sucesso/falha
- Abandono de formulário

### Alertas

#### Configurar no Render

1. Dashboard > Service > Alerts
2. Add Alert Rule:
   - **Condition:** Health check fails
   - **Notification:** Email/Slack/Webhook
   - **Threshold:** 3 failures in 5min

#### Configurar no Vercel

1. Dashboard > Settings > Notifications
2. Enable:
   - Deployment failed
   - Deployment ready
   - Domain configuration issues

#### GitHub Actions

Falhas em CI/CD notificam automaticamente via:
- Email (padrão GitHub)
- Issue creation (em `smoke-test.yml`)

---

## Rollback

### Quando Fazer Rollback

- Health checks falhando consistentemente
- Smoke tests falharam após deploy
- Taxa de erro > 10%
- Funcionalidade crítica quebrada
- Performance degradada (response time > 10s)

### Rollback Automático

**Via Script:**

```bash
# Rollback completo (backend + frontend)
./scripts/deploy/rollback.sh all

# Apenas backend
./scripts/deploy/rollback.sh backend

# Apenas frontend
./scripts/deploy/rollback.sh frontend

# Para versão específica
./scripts/deploy/rollback.sh frontend v1.2.0
```

### Rollback Manual

#### Backend (Render)

1. Dashboard > Service
2. Click em "Manual Deploy"
3. Select "Rollback to Previous"
4. Confirm
5. Aguarde 2-3min
6. Verifique health: `curl https://seu-app.onrender.com/health`

#### Frontend (Vercel)

**Via Dashboard:**
1. Project > Deployments
2. Encontre deployment anterior estável
3. Click "⋯" > "Promote to Production"
4. Confirm
5. Aguarde 1-2min
6. Teste: `curl https://seu-app.vercel.app`

**Via CLI:**
```bash
cd frontend
vercel ls  # Lista deployments
vercel promote <deployment-url>  # Promove específico
```

### Pós-Rollback

1. **Valide estabilidade:**
   ```bash
   ./scripts/deploy/health-check.sh
   ```

2. **Monitore logs por 10-15min**

3. **Investigue causa raiz:**
   - Revise commits da versão com problema
   - Analise logs de erro
   - Reproduza localmente

4. **Crie issue no GitHub:**
   - Título: "Production Rollback - [motivo]"
   - Labels: `bug`, `production`, `urgent`
   - Inclua logs e steps to reproduce

5. **Comunique equipe**

---

## Troubleshooting

### Backend não inicia

**Sintoma:** Health check falha, 503 Service Unavailable

**Checklist:**

1. **Verifique logs:**
   ```bash
   # Render
   Dashboard > Logs > Filter "ERROR"
   
   # Local
   docker-compose logs backend | grep ERROR
   ```

2. **Valide variáveis de ambiente:**
   ```bash
   ./scripts/deploy/check-env.sh
   ```

3. **Teste GOOGLE_API_KEY:**
   ```bash
   curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GOOGLE_API_KEY"
   ```

4. **Verifique dependências:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python -c "import langchain_google_genai; print('OK')"
   ```

5. **Teste localmente:**
   ```bash
   cd backend
   python main.py
   # Deve iniciar em localhost:8000
   ```

### Frontend não carrega

**Sintoma:** Página em branco, erro de carregamento

**Checklist:**

1. **Verifique console do browser:**
   - F12 > Console
   - Procure erros JavaScript

2. **Valide build:**
   ```bash
   cd frontend
   npm run build
   # Deve criar frontend/dist sem erros
   ```

3. **Teste VITE_API_URL:**
   - Abra browser
   - Inspecionar > Network
   - Busque requests para API
   - Verifique se URL está correta

4. **Verifique CORS:**
   ```bash
   curl -H "Origin: https://seu-frontend.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://seu-backend.onrender.com/health -v
   # Deve incluir header Access-Control-Allow-Origin
   ```

5. **Teste localmente:**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Deve abrir em localhost:3000
   ```

### Geração de CV falha

**Sintoma:** Erro 500, timeout, resposta vazia

**Checklist:**

1. **Verifique quota da API:**
   - [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)
   - Gemini API > Quotas
   - Se atingiu limite, aguarde reset ou aumente

2. **Teste endpoint diretamente:**
   ```bash
   curl -X POST https://seu-backend.onrender.com/generate-complete \
     -H "Content-Type: application/json" \
     -d '{
       "cv_text": "João Silva, Python Developer",
       "job_url": "https://example.com/job",
       "tone": "professional",
       "language": "pt-BR"
     }' \
     --max-time 120
   ```

3. **Verifique timeout:**
   - Render: Timeout padrão 300s (5min)
   - Se gerações demoram mais, ajuste timeout:
     ```
     REQUEST_TIMEOUT_SECONDS=600
     ```

4. **Monitore uso de memória:**
   - Render Dashboard > Metrics
   - Se memória > 90%, upgrade plano ou otimize código

5. **Valide entrada:**
   - CV text muito curto (< 100 chars)?
   - URL de vaga acessível?
   - Formato JSON correto?

### Performance lenta

**Sintoma:** Response time > 5s, timeouts frequentes

**Diagnóstico:**

1. **Identifique gargalo:**
   ```bash
   # Teste cada endpoint
   time curl https://seu-backend.onrender.com/health
   time curl -X POST https://seu-backend.onrender.com/extract-job-details -d '...'
   ```

2. **Verifique recursos:**
   - Render: CPU > 80%? Memory > 80%?
   - Se sim, upgrade plano ou otimize

3. **Otimizações possíveis:**
   - Aumentar workers Gunicorn:
     ```bash
     --workers 4  # Ajuste conforme RAM disponível
     ```
   - Habilitar cache (Redis futuro)
   - Otimizar prompts (reduzir tokens)

4. **Cold start:**
   - Render free tier: cold start ~30s
   - Solução: Upgrade para plano pago ou use "keep alive" ping

### CI/CD falha

**Sintoma:** GitHub Actions workflow vermelho

**Checklist:**

1. **Identifique job que falhou:**
   - Actions > Workflow run > Job com ✗

2. **Analise logs:**
   - Click no job com erro
   - Expanda step que falhou
   - Leia mensagem de erro

3. **Erros comuns:**

   **Testes falharam:**
   ```bash
   # Rode localmente
   cd backend
   pytest ../tests/ -v
   # Corrija testes que falharam
   ```

   **Lint errors:**
   ```bash
   cd backend
   ruff check .
   black --check .
   # Corrija e recommit
   ```

   **Build Docker falhou:**
   ```bash
   ./scripts/deploy/build-backend.sh
   # Verifique erros de dependências
   ```

   **Secrets faltando:**
   - GitHub > Settings > Secrets
   - Adicione secrets obrigatórios

4. **Re-run workflow:**
   - Actions > Workflow > Re-run failed jobs

### Logs ausentes ou incompletos

**Problema:** Não consigo ver logs de erro

**Soluções:**

1. **Aumente nível de log temporariamente:**
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Verifique configuração do structlog:**
   - `backend/api/main.py` configura logging
   - Deve usar `JSONRenderer` para produção

3. **Logs locais:**
   ```bash
   docker-compose logs -f --tail=1000 backend > logs.txt
   ```

4. **Render:**
   - Logs mantidos por 7 dias (free)
   - Download via API para archive

---

## Checklist de Produção

Antes de considerar aplicação "production-ready":

### Funcionalidade
- [ ] Health check retorna 200 OK
- [ ] Extração de vaga funciona (teste manual)
- [ ] Geração de CV completo funciona (teste manual)
- [ ] Frontend carrega e interage com backend
- [ ] Smoke tests automatizados passam

### Segurança
- [ ] Secrets configurados e não commitados
- [ ] CORS configurado corretamente
- [ ] API keys rotacionadas recentemente (< 90 dias)
- [ ] Headers de segurança habilitados (X-Frame-Options, etc)
- [ ] Rate limiting configurado

### Performance
- [ ] Health check response < 1s
- [ ] Geração de CV < 60s (p95)
- [ ] Frontend FCP < 2s
- [ ] Cold start < 30s

### Monitoramento
- [ ] Health checks automáticos configurados
- [ ] Logs estruturados funcionando
- [ ] Alertas configurados (email/slack)
- [ ] Métricas sendo coletadas

### CI/CD
- [ ] Workflows GitHub Actions funcionando
- [ ] Deploy automático em push para main
- [ ] Smoke tests pós-deploy configurados
- [ ] Secrets GitHub configurados

### Documentação
- [ ] README atualizado
- [ ] DEPLOY_GUIDE.md revisado
- [ ] Runbooks para incidentes comuns
- [ ] Contatos de emergência documentados

---

## Referências

### Documentação Externa

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [Docker Docs](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [DevOps Guide](https://github.com/Tikam02/DevOps-Guide)

### Documentação Interna

- [README.md](./README.md) - Overview e quickstart
- [scripts/README.md](./scripts/README.md) - Documentação dos scripts
- [tests/README.md](./tests/README.md) - Guia de testes
- [DECISOES_DE_REFATORACAO.md](./DECISOES_DE_REFATORACAO.md) - Decisões técnicas

### Suporte

- **Issues:** [GitHub Issues](https://github.com/seu-usuario/vaga_certa_v2/issues)
- **Render Support:** support@render.com
- **Vercel Support:** support@vercel.com

---

**Versão:** 2.0.0  
**Última atualização:** 2025-11-14  
**Mantenedor:** Equipe Vaga Certa

