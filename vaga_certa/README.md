# Vaga Certa v2

Plataforma inteligente para geração e otimização de materiais de candidatura usando IA (Google Gemini + LangChain).

## Stack Tecnológico

**Backend:**
- Python 3.11+
- FastAPI
- LangChain + Google Gemini
- Web Scraping (BeautifulSoup + httpx)

**Frontend:**
- React 19.2 + TypeScript 5.8
- Vite 6.2
- Tailwind CSS

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- Chave API Google Gemini ([obter aqui](https://aistudio.google.com/app/apikey))

## Quickstart

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env e adicionar GOOGLE_API_KEY
python main.py
```

Backend rodará em: `http://localhost:8000`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend rodará em: `http://localhost:3000`

## Variáveis de Ambiente Essenciais

**Backend (.env):**
- `GOOGLE_API_KEY` - **Obrigatório** - Chave API Google Gemini
- `LANGCHAIN_API_KEY` - Opcional - Para observabilidade (LangSmith)
- `ENVIRONMENT` - development/production
- `API_PORT` - Porta do backend (padrão: 8000)

**Frontend (.env):**
- `VITE_API_URL` - URL do backend (padrão: http://localhost:8000)
- `GEMINI_API_KEY` - Chave Gemini (se usar geração direta no frontend)

## Deploy

### Opção 1: Vercel (Frontend) + Render (Backend)

**Backend (Render):**
1. Conectar repositório
2. Configurar variáveis de ambiente
3. Deploy automático

**Frontend (Vercel):**
1. Conectar repositório
2. Configurar `VITE_API_URL`
3. Deploy automático

### Opção 2: Docker (self-hosted)

```bash
# Backend
cd backend
docker build -t vaga-certa-backend .
docker run -p 8000:8000 --env-file .env vaga-certa-backend

# Frontend
cd frontend
docker build -t vaga-certa-frontend .
docker run -p 3000:3000 vaga-certa-frontend
```

## Estrutura do Projeto

```
vaga_certa_v2/
├── backend/
│   ├── agents/          # Agentes LangChain (extração, geração)
│   ├── api/             # FastAPI endpoints
│   ├── services/        # Web scraping
│   ├── utils/           # Validação, compatibilidade
│   ├── config.py        # Configurações centralizadas
│   ├── main.py          # Entry point
│   └── requirements.txt # Dependências Python
├── frontend/
│   ├── src/
│   │   ├── components/  # Componentes React
│   │   ├── services/    # API clients
│   │   ├── utils/       # Parsers, geradores PDF
│   │   ├── App.tsx      # Componente principal
│   │   └── types.ts     # TypeScript types
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

## Principais Funcionalidades

- **Extração de vagas:** Web scraping automático de URLs de vagas
- **Validação multi-camadas:** Sistema de scoring para qualidade do conteúdo extraído
- **Geração de materiais:** CV otimizado, carta de apresentação, mensagem de networking, dicas de entrevista
- **Análise de compatibilidade:** Score de match candidato-vaga
- **Histórico local:** Armazenamento no navegador

## Endpoints da API

- `GET /` - Status da API
- `GET /health` - Health check
- `POST /extract-job-details` - Extrai detalhes de uma vaga
- `POST /generate-materials` - Gera materiais personalizados
- `POST /generate-complete` - Fluxo completo (extração + geração)

## Troubleshooting

**Backend não inicia:**
- Verificar se `GOOGLE_API_KEY` está configurada no `.env`
- Verificar se porta 8000 não está em uso

**Frontend não conecta ao backend:**
- Verificar se `VITE_API_URL` está correto no `.env` do frontend
- Verificar se backend está rodando

**Erro de CORS:**
- Adicionar origem do frontend em `CORS_ORIGINS` no backend

## Documentação Adicional

- **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)** - Guia completo de deploy, CI/CD e troubleshooting
 - **[DEPLOY_GUIDE_DETAILED.md](DEPLOY_GUIDE_DETAILED.md)** - Guia detalhado para equipes DevOps/SRE com passos exatos e scripts
- [DECISOES_DE_REFATORACAO.md](DECISOES_DE_REFATORACAO.md) - Decisões técnicas da refatoração
- [tests/README.md](tests/README.md) - Guia de testes automatizados
- [scripts/README.md](scripts/README.md) - Documentação dos scripts de deploy

## Licença

MIT

## Versão

2.0.0 - Refatorado para MVP limpo e enxuto, production-ready

