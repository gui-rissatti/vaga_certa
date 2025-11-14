# Suite de Testes - Vaga Certa v2

Estrutura de testes automatizados para garantir qualidade e estabilidade do MVP.

## Estrutura

```
tests/
├── backend/
│   ├── unit/           # Testes unitários (funções, validações, parsers)
│   ├── integration/    # Testes de API endpoints
│   └── e2e/            # Testes end-to-end (fluxo completo)
├── frontend/
│   ├── unit/           # Testes de componentes isolados
│   └── integration/    # Testes de fluxo de UI
├── smoke/              # Testes críticos para produção
├── conftest.py         # Fixtures compartilhadas
└── pytest.ini          # Configuração do pytest
```

## Instalação

```bash
cd backend
pip install -r requirements-test.txt
```

## Executar Testes

### Todos os testes
```bash
pytest
```

### Por categoria
```bash
# Apenas testes unitários (rápidos)
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes E2E (lentos)
pytest -m e2e

# Apenas smoke tests (críticos)
pytest -m smoke
```

### Por diretório
```bash
# Apenas backend
pytest tests/backend/

# Apenas testes unitários do backend
pytest tests/backend/unit/
```

### Com coverage
```bash
pytest --cov=backend --cov-report=html
# Abrir htmlcov/index.html no navegador
```

### Paralelizado (mais rápido)
```bash
pytest -n auto  # Usa todos os cores disponíveis
```

## Escrevendo Testes

### Teste Unitário Exemplo

```python
# tests/backend/unit/test_validation.py
import pytest
from utils.validation import validate_and_score_job_content

@pytest.mark.unit
def test_validate_job_content_valid():
    content = "Desenvolvedor Python Sênior na Tech Corp..."
    result = validate_and_score_job_content(content)
    
    assert result.is_valid
    assert result.score > 0.7
    assert len(result.validation_errors) == 0
```

### Teste de Integração Exemplo

```python
# tests/backend/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.mark.integration
def test_extract_job_details_endpoint():
    client = TestClient(app)
    
    response = client.post("/extract-job-details", json={
        "url": "https://example.com/job",
        "content": "Desenvolvedor Python..."
    })
    
    assert response.status_code == 200
    assert "title" in response.json()
```

### Smoke Test Exemplo

```python
# tests/smoke/test_generate_cv.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.mark.smoke
@pytest.mark.requires_api
def test_generate_complete_cv_success():
    """Teste crítico: geração completa de CV deve funcionar em produção."""
    client = TestClient(app)
    
    response = client.post("/generate-complete", json={
        "cv_text": "João Silva, desenvolvedor Python...",
        "job_url": "https://example.com/job"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "optimized_cv" in data
    assert "cover_letter" in data
    assert len(data["optimized_cv"]) > 100
```

## Markers Disponíveis

- `@pytest.mark.unit` - Testes unitários (rápidos, sem I/O)
- `@pytest.mark.integration` - Testes de integração (APIs, serviços)
- `@pytest.mark.e2e` - Testes end-to-end (fluxo completo)
- `@pytest.mark.smoke` - Testes críticos para validação
- `@pytest.mark.slow` - Testes que demoram > 5s
- `@pytest.mark.requires_api` - Precisam de API keys reais

## CI/CD

Os testes são executados automaticamente via GitHub Actions em cada push/PR:

```yaml
# .github/workflows/backend-ci.yml
- name: Run tests
  run: |
    cd backend
    pytest -m "unit or integration" --cov=backend
```

Smoke tests rodam após deploy:

```yaml
# .github/workflows/smoke-test.yml
- name: Run smoke tests
  run: |
    pytest -m smoke tests/smoke/
```

## Cobertura Mínima

- **Target geral:** 70%
- **Backend crítico (agents, api):** 80%
- **Utils e services:** 60%

## Troubleshooting

**Testes falhando com import error:**
```bash
# Certifique-se de estar na raiz do projeto
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest
```

**Testes lentos:**
```bash
# Execute apenas testes rápidos
pytest -m "not slow"

# Ou paralelizado
pytest -n auto
```

**Coverage baixo:**
```bash
# Veja quais linhas não estão cobertas
pytest --cov=backend --cov-report=term-missing
```

