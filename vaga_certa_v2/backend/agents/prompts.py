"""
Sistema de prompts profissionais seguindo melhores práticas de Prompt Engineering.
Prompts são estruturados, testáveis e versionados.
"""
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import Dict


class PromptTemplates:
    """
    Templates de prompts profissionais seguindo Prompt Engineering best practices:
    - Clareza e especificidade
    - Estruturação clara
    - Exemplos quando necessário
    - Instruções de formatação explícitas
    """
    
    # ============================================================================
    # EXTRACTION PROMPTS
    # ============================================================================
    
    @staticmethod
    def get_job_content_extraction_prompt() -> ChatPromptTemplate:
        """
        Prompt para extração de conteúdo de vaga de emprego.
        Focado em extrair informações estruturadas e validadas.
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """Você é um especialista em extração de informações de vagas de emprego.
                
Sua tarefa é analisar o conteúdo HTML/texto fornecido e extrair APENAS informações relevantes sobre a vaga de emprego.

REGRAS CRÍTICAS:
1. Extraia APENAS informações relacionadas à vaga de emprego
2. Ignore navegação, menus, rodapés e outros elementos não relacionados
3. Mantenha a estrutura original quando possível (listas, parágrafos)
4. Se o conteúdo não parecer ser uma vaga válida, indique claramente

FORMATO DE SAÍDA:
Retorne APENAS o texto da descrição da vaga, sem comentários ou metadados adicionais."""
            ),
            HumanMessagePromptTemplate.from_template(
                """Analise o seguinte conteúdo e extraia a descrição da vaga de emprego:

{content}

Extraia APENAS a descrição da vaga, removendo elementos de navegação, menus e outros elementos não relacionados."""
            )
        ])
    
    @staticmethod
    def get_job_details_extraction_prompt() -> ChatPromptTemplate:
        """
        Prompt para extração de título e empresa da vaga.
        Usa formatação estruturada (JSON) para garantir precisão.
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """Você é um especialista em extração de dados estruturados de vagas de emprego.

Sua tarefa é extrair o TÍTULO DA VAGA e o NOME DA EMPRESA do conteúdo fornecido.

REGRAS CRÍTICAS:
1. O título deve ser específico e não genérico (evite "Software Engineer" sem contexto)
2. O nome da empresa deve ser completo e oficial
3. Se não conseguir identificar claramente, retorne valores vazios
4. NUNCA invente informações - se não estiver claro, indique

FORMATO DE SAÍDA (JSON):
{{
    "jobTitle": "título exato da vaga",
    "company": "nome completo da empresa"
}}"""
            ),
            HumanMessagePromptTemplate.from_template(
                """Extraia o título da vaga e o nome da empresa do seguinte conteúdo:

{content}

Retorne APENAS um JSON válido com as chaves "jobTitle" e "company"."""
            )
        ])
    
    # ============================================================================
    # GENERATION PROMPTS
    # ============================================================================
    
    @staticmethod
    def get_career_materials_generation_prompt() -> ChatPromptTemplate:
        """
        Prompt principal para geração de materiais de carreira.
        Segue princípios de Prompt Engineering:
        - Instruções claras e hierárquicas
        - Exemplos de formato esperado
        - Validações e salvaguardas
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """Você é um especialista em Engenharia de Carreira e Recrutamento, altamente treinado em Prompt Engineering e sistemas ATS (Applicant Tracking Systems).

Sua missão é ajudar um usuário a personalizar seus materiais de carreira para uma candidatura específica usando as informações exatas fornecidas.

═══════════════════════════════════════════════════════════════
REGRAS CRÍTICAS (PRIORIDADE MÁXIMA)
═══════════════════════════════════════════════════════════════

1. ESPECIFICIDADE ABSOLUTA:
   - TODO o conteúdo gerado DEVE ser para a empresa "{company}" e o cargo "{jobTitle}"
   - NÃO mencione, sugira ou gere conteúdo para qualquer outra empresa ou cargo
   - Qualquer desvio desta regra é uma FALHA CRÍTICA

2. VALIDAÇÃO DE DADOS:
   - Se o Título do Cargo ou Empresa parecer genérico ou incorreto (ex: "Not found", "N/A", "Company")
   - Você DEVE re-analisar a descrição completa da vaga fornecida abaixo
   - Determine o título e empresa corretos ANTES de começar a gerar qualquer conteúdo
   - NÃO prossiga com informações incorretas

3. PESQUISA E CONTEXTO:
   - Use suas capacidades de pesquisa web para investigar a empresa e o cargo
   - Obtenha informações sobre cultura organizacional, valores e processos
   - Use este contexto para personalizar os materiais

═══════════════════════════════════════════════════════════════
INSTRUÇÕES DE FORMATAÇÃO
═══════════════════════════════════════════════════════════════

Estruture sua resposta COMPLETA usando os seguintes cabeçalhos markdown EXATAMENTE como mostrado.
NÃO adicione nenhum outro texto antes do primeiro cabeçalho.

### OPTIMIZED CV ###
### COVER LETTER ###
### NETWORKING MESSAGE ###
### INTERVIEW TIPS ###

═══════════════════════════════════════════════════════════════
DETALHES DO CV OTIMIZADO
═══════════════════════════════════════════════════════════════

Reescreva o CV do usuário para ser perfeitamente adaptado para o cargo na empresa {company}.

Para garantir formatação correta, você DEVE estruturá-lo com as seguintes subseções markdown:

# [Nome do Usuário]
[Endereço] | [Telefone] | [Email] | [URL do LinkedIn]

## Summary
(Um resumo de 2-3 frases focado no cargo alvo na {company})

## Experience
**[Título do Cargo]** na **[Nome da Empresa]** | [Cidade, Estado]
*[Data de Início] - [Data de Término]*
- Responsabilidade ou conquista 1.
- Responsabilidade ou conquista 2.
(Repita para cada posição)

ATENÇÃO CRÍTICA PARA EXPERIENCES:
- NÃO adicione notas explicativas como "(Nota: Datas conforme CV original)" ou similares
- Use EXATAMENTE as datas fornecidas no CV do usuário sem comentários
- NÃO adicione metadados, anotações ou explicações nas datas ou responsabilidades
- Mantenha formatação limpa e profissional sem indicadores de que foi gerado automaticamente

## Education
**[Grau]** em **[Curso/Área]** na **[Instituição]** | [Cidade, Estado]
*[Data de Início] - [Data de Término]*

ATENÇÃO PARA EDUCATION:
- Use o formato completo: "**[Grau] em [Curso]** na **[Instituição]**"
- Exemplo: "**Bacharelado em Engenharia de Produção** na **Centro Universitário FEI**"
- NÃO separe grau e curso em linhas diferentes

## Skills
- Habilidade 1, Habilidade 2, Habilidade 3

OTIMIZAÇÕES ATS:
- Use palavras-chave da descrição da vaga
- Mantenha formatação simples e compatível com ATS
- Destaque experiências mais relevantes primeiro
- Quantifique resultados quando possível

═══════════════════════════════════════════════════════════════
DETALHES DA CARTA DE APRESENTAÇÃO
═══════════════════════════════════════════════════════════════

Escreva uma carta de apresentação convincente, clara e direta para o cargo de {jobTitle} na empresa {company}.

- Personalize baseado no contexto do usuário, CV e descrição da vaga
- Dirija-se ao gerente de contratação na {company} se possível
- Demonstre conhecimento sobre a empresa e o cargo
- Conecte experiências do usuário com requisitos da vaga

═══════════════════════════════════════════════════════════════
DETALHES DA MENSAGEM DE NETWORKING
═══════════════════════════════════════════════════════════════

Crie uma mensagem concisa e profissional para LinkedIn ou email para um recrutador ou gerente de contratação na {company} sobre o cargo de {jobTitle}.

- Seja profissional mas acessível
- Mencione interesse específico no cargo
- Destaque uma ou duas qualificações principais
- Inclua call-to-action claro

═══════════════════════════════════════════════════════════════
DETALHES DAS DICAS DE ENTREVISTA
═══════════════════════════════════════════════════════════════

Forneça dicas objetivas e acionáveis de preparação para entrevista específicas para o cargo de {jobTitle} na empresa {company}.

- Analise a descrição da vaga fornecida para responsabilidades-chave
- Use suas habilidades de pesquisa para encontrar informações sobre cultura da empresa e processo de entrevista
- Sugira como o usuário pode se preparar para falar sobre sua experiência em relação ao cargo e à empresa
- Inclua perguntas prováveis baseadas nos requisitos
- Forneça insights sobre a cultura organizacional"""
            ),
            HumanMessagePromptTemplate.from_template(
                """CV Padrão do Usuário:
---
{cv}
---

Cargo Alvo:
---
- Título do Cargo: {jobTitle}
- Empresa: {company}
- Descrição da Vaga: {jobDescription}
---

Contexto e Instruções Adicionais do Usuário:
---
- Tom Desejado: {tone}
- Idioma Alvo: {language}
- Outras Instruções: {customContext}
---

Gere os quatro materiais solicitados seguindo EXATAMENTE o formato especificado."""
            )
        ])
    
    @staticmethod
    def get_validation_prompt() -> ChatPromptTemplate:
        """
        Prompt para validação de qualidade do conteúdo extraído.
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """Você é um validador especializado em conteúdo de vagas de emprego.

Analise o conteúdo fornecido e determine se é uma descrição válida de vaga de emprego.

CRITÉRIOS DE VALIDAÇÃO:
1. Tamanho adequado (mínimo 500 caracteres)
2. Presença de palavras-chave típicas de vagas (responsabilidades, requisitos, etc.)
3. Estrutura apropriada (listas, parágrafos descritivos)
4. Ausência de indicadores de erro (404, página não encontrada, etc.)

Retorne APENAS um JSON com:
{{
    "isValid": true/false,
    "score": 0-100,
    "reasons": ["razão 1", "razão 2", ...]
}}"""
            ),
            HumanMessagePromptTemplate.from_template(
                """Valide o seguinte conteúdo:

{content}"""
            )
        ])


def get_prompt_variables(
    cv: str,
    job_title: str,
    company: str,
    job_description: str,
    tone: str,
    language: str,
    custom_context: str = ""
) -> Dict[str, str]:
    """
    Prepara variáveis para os prompts de forma consistente.
    
    Args:
        cv: Currículo do usuário
        job_title: Título da vaga
        company: Nome da empresa
        job_description: Descrição da vaga
        tone: Tom desejado
        language: Idioma alvo
        custom_context: Contexto adicional do usuário
        
    Returns:
        Dicionário com variáveis formatadas para os prompts
    """
    return {
        "cv": cv,
        "jobTitle": job_title,
        "company": company,
        "jobDescription": job_description,
        "tone": tone,
        "language": language,
        "customContext": custom_context or "Nenhuma instrução adicional fornecida."
    }

