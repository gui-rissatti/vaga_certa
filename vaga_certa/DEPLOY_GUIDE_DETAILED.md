# Guia de Deploy Detalhado — Vaga Certa (DevOps / SRE)

Guia step-by-step voltado a Engenheiros DevOps, SREs e quem será responsável por fazer deploys em produção.

## Objetivo
Criar um passo-a-passo reproduzível para:
- Preparar o ambiente local para testes
- Construir imagens Docker
- Subir a aplicação localmente via Docker Compose
- Fazer deploy para Render (backend) e Vercel (frontend)
- Configurar CI/CD com GitHub Actions
- Configurar monitoramento, alarmes e rollback

> Público-alvo: Engenheiros DevOps, SREs, engenheiros backend com experiência em cloud.

---

## 1) Pré-requisitos (versões testadas)

- Git >= 2.30
- Docker 20.10+ e Docker Compose 2.x
- Python 3.11+
- Node.js 18+
- gh (GitHub CLI) — opcional, recomendado
- Conta em Render e Vercel
- Acesso para adicionar Secrets no GitHub repo

## 2) Passo-a-passo — Setup local e validação

1) Clone do repositório e navegue para a raiz do projeto

```powershell
git clone https://github.com/gui-rissatti/vaga_certa.git
cd vaga_certa
```

2) Validar arquivos e ambiente

- Verifique `.env.example` nas pastas `backend/` e `frontend/`.
- No Windows (PowerShell) copie os arquivos de exemplo para `.env` com:

```powershell
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3) Backend — Virtualenv (opcional, local dev)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4) Frontend — Dependências

```powershell
cd ../frontend
npm ci
```

5) Teste rápido local (backend)

```powershell
cd ../backend
python main.py
# ou, para behaviour mais similar a produção:
gunicorn api.main:app --bind 0.0.0.0:8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker
```

Abra `http://localhost:8000/docs` para validar endpoints.

---

## 3) Docker — Build e execução local (ex. test pré-deploy)

1) Build de imagens (local):

```powershell
docker build -t vaga-certa-backend:local ./backend
docker build -t vaga-certa-frontend:local ./frontend
```

2) Rodar via docker-compose (recomendado):

```powershell
docker-compose up -d --build
docker-compose logs -f backend
```

3) Status de saúde

```powershell
docker-compose ps
curl http://localhost:8000/health
```

4) Fechar/limpar

```powershell
docker-compose down --volumes
```

---

## 4) Deploy para Render (Backend)

Pré-configuração:

- Crie um Web Service em Render 
- Root Directory: `backend`
- Environment: `Python 3`

Build command (Render):

```text
pip install --upgrade pip && pip install -r requirements.txt
```

Start command (Render — use Gunicorn para produção):

```text
gunicorn api.main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 300
```

Env vars recomendadas:

- `GOOGLE_API_KEY` (obrigatório)
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `CORS_ORIGINS=https://seu-frontend.example.com`

Testes pós-deploy:

```bash
curl -f https://seu-app.onrender.com/health
# se falhar, verifique logs no Render e o build output
```

---

## 5) Deploy Frontend (Vercel)

1) Import repository para Vercel

2) Config:

- Framework: Vite
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output: `dist`

3) Adicione Secret `VITE_API_URL` apontando para a URL de backend. No Vercel, também configure Environment variables `VITE_API_URL` para produção e preview.

---

## 6) CI / CD com GitHub Actions – detalhes (como configurar)

1) Secrets no GitHub: `Settings -> Secrets and variables -> Actions`

Adicionar:

- `GOOGLE_API_KEY`
- `GOOGLE_API_KEY_TEST`
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID_PRODUCTION`
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `PRODUCTION_BACKEND_URL` & `PRODUCTION_FRONTEND_URL`

2) Exemplo: adicionar via `gh` (CLI):

```powershell
gh secret set GOOGLE_API_KEY --body "<sua-key>"
gh secret set RENDER_API_KEY --body "<seu-token-render>"
gh secret set VERCEL_TOKEN --body "<seu-token-vercel>"
```

3) Como o pipeline executa:

- `backend-ci.yml` — lint, test, build, deploy Render
- `frontend-ci.yml` — build, artefatos, deploy Vercel
- `smoke-test.yml` — pós-deploy valida endpoints críticos

4) Dicas práticas

- Teste suas secrets usando `gh run` e `workflow_dispatch` para executar os workflows manualmente (útil durante setup inicial)
- Ative `Auto-deploy` em Render/Vercel quando `main` for atualizado

---

## 7) Monitoramento, logs e alertas

- Configure health check em Render para `/health` com interval=30s
- Configure Alertas no Render (Health check fail) e na Vercel (build failed)
- Configure LangSmith (opcional) para observabilidade de requisições

---

## 8) Rollback e recuperação

1) Render: Revert to previous deploy from Render UI (deploy list)

2) Git-based rollback

```powershell
git checkout main
git revert <SHA-PRINCIPAL> -m 1
git push origin main
# GHA desencadeará novo deploy de rollback
```

3) Manual rollback com Docker: rodar a tag anterior localmente para validar.

---

## 9) Troubleshooting (comandos úteis)

- Ver logs do backend no Compose:

```powershell
docker-compose logs -f backend
```

- Validar health endpoint:

```powershell
curl -v http://localhost:8000/health
```

- Validar config no GitHub Actions:

```powershell
gh workflow run "Backend CI/CD" --ref main --field environment=production
```

---

## 10) Checklist de produção (passo-a-passo final antes do deploy)

1) Validar secrets no GitHub
2) Testar build localmente com docker-compose
3) Rodar CI localmente se possível (simular pipelines)
4) Criar release/PR e revisar pipeline no GitHub
5) Validar smoke tests pós-deploy

---

## Referências

- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- GitHub Actions: https://docs.github.com/actions

---

Se quiser, eu posso também criar uma versão exclusiva para operadores menos técnicos (por exemplo, produto ou suporte) com passos ainda mais simplificados e checklists.
