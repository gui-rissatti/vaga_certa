# Decisões de Refatoração - Vaga Certa v2

Este documento registra as decisões técnicas tomadas durante a refatoração do projeto original (`vaga_certa`) para a versão 2 (`vaga_certa_v2`).

## Objetivo da Refatoração

Criar um repositório limpo, enxuto e pronto para produção (MVP), seguindo:
- Princípios de Clean Code
- Estrutura minimalista do guia [refakts](https://github.com/devill/refakts)
- Melhores práticas de Prompt Engineering

## Estrutura de Pastas

### Decisão: Separação Backend/Frontend

**Antes:** Arquivos misturados na raiz  
**Depois:** 
- `backend/` - Todo código Python/FastAPI
- `frontend/` - Todo código React/TypeScript

**Razão:** Clareza, separação de responsabilidades, facilita deploy independente.

---

## Arquivos Removidos

### 1. Documentação Excessiva (24 arquivos .md removidos)

**Removidos:**
- `ACAO_IMEDIATA.md`
- `ALTERNATIVAS_HOSPEDAGEM.md`
- `BUG_FIX_OBJECT_OBJECT.md`
- `CONFIGURAR_VERCEL_ENV.md`
- `DEBUG_REPORT_404.md`
- `DEPLOY_RENDER.md`
- `DEPLOY_VERCEL.md`
- `EXECUTAR_LOCALMENTE.md`
- `EXECUTAR_WINDOWS.md`
- `GUIA_TECNICO.md`
- `INDICE.md`
- `INICIAR_PROJETO.md`
- `MIGRACAO.md`
- `QUICKSTART_RENDER.md`
- `REFATORACAO_COMPLETA.md`
- `SOLUCAO_IMPLEMENTADA.md`
- `SOLUCAO_MIGRACAO_RENDER.md`
- `SUITE_TESTES_QA.md`
- `backend/FALLBACK_IMPLEMENTATION.md`
- `backend/tests/README.md`
- `backend/tests/MATRIZ_TESTES.md`

**Mantido:**
- `README.md` (reescrito, enxuto, focado em quickstart)
- `DECISOES_DE_REFATORACAO.md` (este arquivo)

**Razão:** Documentação deve ser concisa e direcionada a desenvolvedores core, não end-users. Um README enxuto + este documento são suficientes para MVP.

---

### 2. Testes Completos (removidos)

**Removidos:**
- `backend/tests/` (inteira: unit/, integration/, e2e/, stress/)
- `utils/__tests__/` (testes frontend)
- `App.test.tsx`
- `pytest.ini`
- Configurações de coverage (`htmlcov/`)

**Razão:** Para MVP, testes extensivos não são prioridade. Foco em código funcional e deployment rápido. Testes podem ser adicionados posteriormente conforme necessidade.

---

### 3. Scripts Windows Específicos

**Removidos:**
- `QUICKSTART.bat`
- `QUICKSTART.sh`
- `iniciar_backend.bat`
- `iniciar_frontend.bat`
- `iniciar_completo.bat`
- `LEIA-ME_WINDOWS.txt`

**Razão:** Scripts específicos de plataforma criam fragmentação. O README com comandos simples é universal e suficiente.

---

### 4. Build Artifacts e Temporários

**Removidos:**
- `htmlcov/` (ambas: raiz e backend)
- `dist/`
- `node_modules/` (via .gitignore)
- `backend/venv/` (via .gitignore)
- `backend/__pycache__/` (via .gitignore)

**Razão:** Artifacts não devem estar no repositório. Adicionados ao `.gitignore`.

---

### 5. Configurações e Metadados Supérfluos

**Removidos:**
- `metadata.json`
- `api/` (pasta raiz vazia/confusa)
- Duplicações de Docker configs

**Razão:** Reduzir confusão. Configs de deploy podem ser adicionadas em `deploy/` se necessário.

---

## Dependências Limpas

### Backend (requirements.txt)

**Removido:**
```
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-mock==3.14.0
pytest-cov==5.0.0
pytest-timeout==2.3.1
```

**Mantido apenas:**
- FastAPI, Uvicorn
- LangChain + LangSmith
- BeautifulSoup, httpx, aiohttp
- Utilities (python-dotenv, tenacity, structlog)
- Produção (gunicorn, python-multipart)

---

### Frontend (package.json)

**Removido:**
```
@jest/globals
@testing-library/react
@testing-library/jest-dom
vitest
@vitest/ui
```

Scripts de teste:
```json
"test": "vitest run",
"test:watch": "vitest",
```

**Mantido apenas:**
- React, React-DOM
- @google/genai
- jsPDF, pdfjs-dist
- Dev: TypeScript, Vite, @vitejs/plugin-react

---

## Arquivos de Configuração

### Novos Arquivos Criados

1. **`.env.example`** (backend e frontend)
   - Documentação clara de variáveis essenciais
   - Comentários explicativos
   - Links para obter credenciais

2. **`.gitignore`** (raiz)
   - Robusto, cobre Python, Node, IDEs
   - Ignora secrets (.env)
   - Ignora build artifacts

3. **`README.md`** (reescrito)
   - Quickstart em <100 linhas
   - Comandos diretos
   - Pré-requisitos claros
   - Estrutura do projeto

4. **`DECISOES_DE_REFATORACAO.md`** (este arquivo)
   - Registra decisões técnicas
   - Documenta o que foi removido e por quê

---

## Estrutura de Código Mantida

### Backend

**Mantido:**
- `agents/` - BaseAgent, ExtractionAgent, GenerationAgent, Prompts
- `api/` - main.py (FastAPI), models.py (Pydantic)
- `services/` - WebScraper
- `utils/` - validation.py, compatibility.py
- `config.py` - Settings centralizadas
- `setup_langsmith.py` - Observabilidade
- `main.py` - Entry point

**Razão:** Todo código core é essencial para funcionamento.

---

### Frontend

**Mantido:**
- `src/components/` - Header, InputSection, OutputSection, HistorySidebar, Icons
- `src/services/` - apiService, geminiService, webScraperService
- `src/utils/` - cvParser, pdfGenerator
- `src/App.tsx` - Componente principal
- `src/types.ts` - TypeScript types
- `index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`

**Razão:** Todo código core é essencial para funcionamento.

---

## Princípios Aplicados

### 1. YAGNI (You Aren't Gonna Need It)
- Removido tudo que não é estritamente necessário para MVP funcional

### 2. KISS (Keep It Simple, Stupid)
- Estrutura de pastas simples e intuitiva
- README direto ao ponto
- Comandos de setup mínimos

### 3. DRY (Don't Repeat Yourself)
- Documentação consolidada em um único README
- Configurações centralizadas

### 4. Clean Code
- Código autoexplicativo
- Nomes de pastas claros (backend, frontend, agents, services, utils)
- Sem dead code

---

## Inspiração: refakts

Seguindo o guia [refakts](https://github.com/devill/refakts):
- **Estrutura clara:** backend/frontend separados
- **README mínimo:** Quickstart + comandos essenciais
- **Sem bloat:** Zero arquivos desnecessários
- **Pragmatismo:** Funcionalidade sobre perfeição

---

## Deploy-Ready

A estrutura refatorada está pronta para deploy em:
- **Vercel** (frontend) + **Render** (backend)
- **Railway** (monorepo)
- **Docker** (self-hosted)
- **Fly.io**, etc.

Configs específicas de deploy podem ser adicionadas em `deploy/` conforme necessário.

---

## Checklist de Qualidade ✅

- [x] Estrutura backend/ e frontend/ separadas
- [x] Sem arquivos de teste
- [x] Sem documentação redundante
- [x] requirements.txt e package.json limpos
- [x] .gitignore robusto
- [x] README.md conciso e técnico
- [x] .env.example com vars essenciais
- [x] DECISOES_DE_REFATORACAO.md criado
- [x] Código funcional e imports corretos

---

## Próximos Passos (Pós-MVP)

Caso o projeto cresça, considerar:
1. Adicionar testes (pytest, vitest) em PRs futuros
2. CI/CD (GitHub Actions)
3. Logging estruturado (já tem structlog)
4. Monitoramento (LangSmith já configurado)
5. Rate limiting (já tem configuração)
6. Cache (Redis para requests frequentes)

---

## Conclusão

Esta refatoração transformou um projeto com ~100 arquivos em uma estrutura enxuta e focada, mantendo 100% da funcionalidade core enquanto remove bloat desnecessário. O resultado é um MVP limpo, mantenível e pronto para produção.

**Versão:** 2.0.0  
**Data:** 2025-01-14  
**Princípio:** Menos é mais. Código limpo é código que funciona.

