import { GoogleGenAI, Type } from "@google/genai";
import type { UserInput, GeneratedContent, GroundingSource, JobDetails } from '../types';

// IMPORTANT: Do not expose this key publicly.
// It is assumed that process.env.API_KEY is configured in the build environment.
const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY environment variable not set.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

const TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes
const MAX_RETRIES = 3;
const BASE_RETRY_DELAY_MS = 2000; // 2 seconds

// ============================================================================
// LOGGING & TELEMETRY
// ============================================================================

interface ExtractionLog {
  timestamp: string;
  operation: string;
  attempt: number;
  success: boolean;
  confidenceScore?: number;
  error?: string;
  duration?: number;
}

const logs: ExtractionLog[] = [];

const logExtraction = (log: Omit<ExtractionLog, 'timestamp'>) => {
  const entry = { ...log, timestamp: new Date().toISOString() };
  logs.push(entry);
  console.log(`[EXTRACTION LOG] ${JSON.stringify(entry)}`);
};

export const getExtractionLogs = () => [...logs];

// ============================================================================
// UTILITIES
// ============================================================================

const withTimeout = <T,>(promise: Promise<T>, message: string): Promise<T> => {
  const timeout = new Promise<T>((_, reject) => {
    const id = setTimeout(() => {
      clearTimeout(id);
      reject(new Error(message));
    }, TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]);
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Wrapper para retry com backoff exponencial.
 * Trata falhas temporárias de rede e instabilidades da API.
 */
const withRetry = async <T,>(
  operation: (attempt: number) => Promise<T>,
  operationName: string,
  maxRetries: number = MAX_RETRIES
): Promise<T> => {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const startTime = Date.now();
      const result = await operation(attempt);
      const duration = Date.now() - startTime;
      
      logExtraction({
        operation: operationName,
        attempt,
        success: true,
        duration
      });
      
      return result;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      logExtraction({
        operation: operationName,
        attempt,
        success: false,
        error: lastError.message
      });
      
      if (attempt < maxRetries) {
        const delay = BASE_RETRY_DELAY_MS * Math.pow(2, attempt - 1);
        console.warn(`[${operationName}] Attempt ${attempt} failed: ${lastError.message}. Retrying in ${delay}ms...`);
        await sleep(delay);
      }
    }
  }
  
  throw new Error(`${operationName} failed after ${maxRetries} attempts. Last error: ${lastError?.message}`);
};

// ============================================================================
// VALIDATION & CONFIDENCE SCORING
// ============================================================================

interface ValidationResult {
  isValid: boolean;
  score: number; // 0-100
  reasons: string[];
}

/**
 * Valida e pontua o conteúdo extraído de uma vaga.
 * Sistema de scoring multi-camadas (estrutural 30pts + semântico 40pts + heurística 30pts).
 * Threshold mínimo de 70% para aprovar qualidade.
 * 
 * Camadas:
 * 1. Estrutural: Tamanho e formato básico
 * 2. Semântica: Palavras-chave de contexto de vaga
 * 3. Heurística: Densidade de informação e coerência
 */
const validateAndScoreJobContent = (content: string): ValidationResult => {
  const reasons: string[] = [];
  let score = 0;

  // === LAYER 1: STRUCTURAL VALIDATION (30 points) ===
  if (!content || content.trim().length === 0) {
    return { isValid: false, score: 0, reasons: ["Conteúdo vazio"] };
  }

  const length = content.trim().length;
  
  // Tamanho mínimo robusto (vagas têm pelo menos 500 caracteres)
  if (length < 500) {
    reasons.push(`Conteúdo muito curto (${length} chars, mínimo 500)`);
  } else if (length < 1000) {
    score += 10;
    reasons.push("Tamanho aceitável mas curto");
  } else if (length < 3000) {
    score += 20;
    reasons.push("Tamanho adequado");
  } else {
    score += 30;
    reasons.push("Tamanho excelente");
  }

  // === LAYER 2: SEMANTIC VALIDATION (40 points) ===
  const contentLower = content.toLowerCase();
  
  // Palavras-chave de vaga (alta prioridade)
  const criticalJobKeywords = [
    'responsibilities', 'requirements', 'qualifications', 'experience',
    'responsabilidades', 'requisitos', 'qualificações', 'experiência'
  ];
  
  const hasCriticalKeywords = criticalJobKeywords.filter(kw => contentLower.includes(kw)).length;
  const criticalScore = Math.min(20, hasCriticalKeywords * 5);
  score += criticalScore;
  reasons.push(`${hasCriticalKeywords}/8 palavras-chave críticas encontradas (${criticalScore} pts)`);
  
  // Contexto de recrutamento
  const contextKeywords = [
    'apply', 'application', 'candidate', 'candidatar', 'aplicar',
    'join', 'team', 'position', 'role', 'vaga', 'cargo', 'equipe'
  ];
  
  const hasContextKeywords = contextKeywords.filter(kw => contentLower.includes(kw)).length;
  const contextScore = Math.min(20, hasContextKeywords * 2);
  score += contextScore;
  reasons.push(`${hasContextKeywords}/12 palavras de contexto encontradas (${contextScore} pts)`);

  // === LAYER 3: HEURISTIC VALIDATION (30 points) ===
  
  // Densidade de informação (evita textos genéricos ou repetitivos)
  const words = content.split(/\s+/).filter(w => w.length > 3);
  const uniqueWords = new Set(words.map(w => w.toLowerCase()));
  const diversityRatio = uniqueWords.size / words.length;
  
  if (diversityRatio > 0.5) {
    score += 15;
    reasons.push(`Boa diversidade lexical (${(diversityRatio * 100).toFixed(1)}%)`);
  } else if (diversityRatio > 0.3) {
    score += 8;
    reasons.push(`Diversidade lexical moderada (${(diversityRatio * 100).toFixed(1)}%)`);
  } else {
    reasons.push(`Baixa diversidade lexical (${(diversityRatio * 100).toFixed(1)}%) - possível texto repetitivo`);
  }
  
  // Detecta indicadores de erro
  const errorIndicators = [
    'page not found', '404', 'error', 'not available',
    'página não encontrada', 'erro', 'indisponível', 'access denied'
  ];
  
  const hasErrorIndicators = errorIndicators.some(indicator => contentLower.includes(indicator));
  
  if (hasErrorIndicators) {
    score = Math.max(0, score - 30);
    reasons.push("⚠️ Detectados indicadores de erro na página");
  } else {
    score += 15;
    reasons.push("Nenhum indicador de erro detectado");
  }

  // Verifica estrutura básica de listagem (bullet points, numeração)
  const hasListStructure = /[-•*]\s|^\d+\.\s/m.test(content);
  if (hasListStructure) {
    reasons.push("✓ Estrutura de lista detectada (típico de vagas)");
  }

  const isValid = score >= 70;
  
  return { isValid, score, reasons };
};

/**
 * Valida e pontua detalhes extraídos (título e empresa).
 * Validação rigorosa com blacklist de termos genéricos.
 * Threshold de 90% requer ambos título e empresa válidos.
 */
const validateAndScoreJobDetails = (
  jobTitle: string, 
  company: string
): ValidationResult => {
  const reasons: string[] = [];
  let score = 0;

  const genericTerms = [
    'not found', 'n/a', 'na', 'unknown', 'tbd', 'to be determined', 
    'não encontrado', 'desconhecido', 'error', 'none', 'null'
  ];
  const normalizedGenerics = new Set(
    genericTerms.map(term => term.toLowerCase().replace(/[^a-z0-9]+/g, ''))
  );
  
  const titleLower = jobTitle?.toLowerCase().trim() || '';
  const companyLower = company?.toLowerCase().trim() || '';

  // Validação de título
  if (!jobTitle || titleLower.length === 0) {
    return { isValid: false, score: 0, reasons: ["Título da vaga ausente"] };
  }
  
  const normalizedTitle = (jobTitle || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  if (normalizedGenerics.has(normalizedTitle)) {
    return { isValid: false, score: 0, reasons: [`Título genérico/inválido: "${jobTitle}"`] };
  }
  
  if (titleLower.length < 5) {
    reasons.push(`Título muito curto: "${jobTitle}"`);
  } else if (titleLower.length > 100) {
    reasons.push(`Título muito longo: "${jobTitle}"`);
  } else {
    score += 50;
    reasons.push("✓ Título válido");
  }

  // Validação de empresa
  if (!company || companyLower.length === 0) {
    return { isValid: false, score: 0, reasons: ["Nome da empresa ausente"] };
  }
  
  const normalizedCompany = (company || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  if (normalizedGenerics.has(normalizedCompany)) {
    return { isValid: false, score: 0, reasons: [`Empresa genérica/inválida: "${company}"`] };
  }
  
  if (companyLower.length < 2) {
    reasons.push(`Nome da empresa muito curto: "${company}"`);
  } else if (companyLower.length > 100) {
    reasons.push(`Nome da empresa muito longo: "${company}"`);
  } else {
    score += 50;
    reasons.push("✓ Empresa válida");
  }

  const isValid = score >= 90; // Requer ambos título e empresa válidos
  
  return { isValid, score, reasons };
};

/**
 * Valida se o conteúdo extraído parece ser de uma vaga de emprego válida.
 * Retorna true se passar em todas as validações, false caso contrário.
 * @deprecated Use validateAndScoreJobContent instead
 */
const validateJobContent = (content: string): { isValid: boolean; reason?: string } => {
  if (!content || content.trim().length === 0) {
    return { isValid: false, reason: "Conteúdo vazio" };
  }

  // Verifica tamanho mínimo (vagas geralmente têm pelo menos 200 caracteres)
  if (content.trim().length < 200) {
    return { isValid: false, reason: "Conteúdo muito curto para ser uma descrição de vaga válida" };
  }

  // Verifica se contém palavras-chave típicas de vagas
  const jobKeywords = [
    'responsibilities', 'requirements', 'qualifications', 'experience',
    'responsabilidades', 'requisitos', 'qualificações', 'experiência',
    'job', 'position', 'role', 'vaga', 'cargo', 'posição',
    'apply', 'application', 'candidatar', 'aplicar'
  ];
  
  const contentLower = content.toLowerCase();
  const hasJobKeywords = jobKeywords.some(keyword => contentLower.includes(keyword));
  
  if (!hasJobKeywords) {
    return { isValid: false, reason: "Conteúdo não contém palavras-chave típicas de vagas de emprego" };
  }

  // Verifica se não parece ser uma página de erro ou genérica
  const errorIndicators = [
    'page not found', '404', 'error', 'not available',
    'página não encontrada', 'erro', 'indisponível'
  ];
  
  const hasErrorIndicators = errorIndicators.some(indicator => 
    contentLower.includes(indicator) && contentLower.length < 500
  );
  
  if (hasErrorIndicators) {
    return { isValid: false, reason: "Conteúdo parece ser uma página de erro" };
  }

  return { isValid: true };
};

/**
 * Valida se o título e empresa extraídos são válidos e não genéricos.
 */
const validateJobDetails = (jobTitle: string, company: string): { isValid: boolean; reason?: string } => {
  const genericTitles = ['not found', 'n/a', 'na', 'unknown', 'tbd', 'to be determined', 'não encontrado', 'desconhecido'];
  const genericCompanies = ['not found', 'n/a', 'na', 'unknown', 'company', 'empresa', 'não encontrado', 'desconhecido'];

  const titleLower = jobTitle?.toLowerCase().trim() || '';
  const companyLower = company?.toLowerCase().trim() || '';

  if (!jobTitle || titleLower.length === 0) {
    return { isValid: false, reason: "Título da vaga não foi extraído" };
  }

  if (!company || companyLower.length === 0) {
    return { isValid: false, reason: "Nome da empresa não foi extraído" };
  }

  if (genericTitles.some(gt => titleLower.includes(gt))) {
    return { isValid: false, reason: `Título da vaga parece genérico ou inválido: "${jobTitle}"` };
  }

  if (genericCompanies.some(gc => companyLower.includes(gc))) {
    return { isValid: false, reason: `Nome da empresa parece genérico ou inválido: "${company}"` };
  }

  // Verifica se o título tem tamanho razoável (não muito curto, não muito longo)
  if (titleLower.length < 3 || titleLower.length > 100) {
    return { isValid: false, reason: `Título da vaga tem tamanho inválido: "${jobTitle}"` };
  }

  // Verifica se a empresa tem tamanho razoável
  if (companyLower.length < 2 || companyLower.length > 100) {
    return { isValid: false, reason: `Nome da empresa tem tamanho inválido: "${company}"` };
  }

  return { isValid: true };
};

/**
 * Extrai conteúdo da descrição de vaga usando web scraping direto.
 * 
 * Estratégia:
 * 1. Web scraping via fetch API + HTML parsing
 * 2. Fallback automático para proxies CORS se necessário
 * 3. Validação multi-camada com confidence scoring (threshold 70%)
 * 4. Rejeita extrações de baixa qualidade
 * 
 * Nota: IA é usada exclusivamente para geração de conteúdo personalizado,
 * não para extração de dados.
 */
export const extractJobContentFromUrl = async (jobUrl: string): Promise<string> => {
  if (!jobUrl) {
    throw new Error("Job URL cannot be empty.");
  }

  // Validação básica da URL
  try {
    new URL(jobUrl);
  } catch {
    throw new Error(`URL inválida fornecida: "${jobUrl}"`);
  }

  return withRetry(async (attempt) => {
    console.log(`🔍 Tentativa ${attempt}/3: Extraindo conteúdo via web scraping de ${jobUrl}`);
    
    // Importa o web scraper direto (ÚNICO método disponível)
    const { scrapeJobPosting } = await import('./webScraperService');
    
    // Faz scraping direto (throws error se falhar)
    const scrapedData = await scrapeJobPosting(jobUrl);
    
    const description = scrapedData.fullText.trim();
    
    if (!description || description.length < 100) {
      throw new Error(
        "❌ Web scraper retornou conteúdo insuficiente.\n\n" +
        "Possíveis causas:\n" +
        "• Página exige autenticação (login)\n" +
        "• Conteúdo é carregado por JavaScript\n" +
        "• URL bloqueada por CORS/firewall\n\n" +
        "💡 Tente outra URL ou cole a descrição manualmente."
      );
    }

    // VALIDAÇÃO COM SCORING: Rejeita se score < 70%
    const validation = validateAndScoreJobContent(description);
    
    logExtraction({
      operation: 'extractJobContentFromUrl',
      attempt,
      success: validation.isValid,
      confidenceScore: validation.score,
      error: validation.isValid ? undefined : validation.reasons.join('; ')
    });
    
    if (!validation.isValid) {
      const reasonsSummary = validation.reasons.join(' | ');
      throw new Error(
        `❌ VALIDAÇÃO FALHOU (Score: ${validation.score}/100, mínimo: 70)\n\n` +
        `Motivos: ${reasonsSummary}\n\n` +
        `🔍 O conteúdo extraído não parece ser uma descrição de vaga válida.\n` +
        `Verifique se a URL realmente leva a uma página de vaga de emprego.\n\n` +
        `💡 Soluções:\n` +
        `• Tente outra URL da mesma vaga\n` +
        `• Cole a descrição da vaga manualmente`
      );
    }

    console.log(`✅ Extração validada com sucesso! Score: ${validation.score}/100`);
    console.log(`• Título: "${scrapedData.title}"`);
    console.log(`• Empresa: "${scrapedData.company}"`);
    console.log(`• Detalhes: ${validation.reasons.join(' | ')}`);
    
    return description;

  }, 'extractJobContentFromUrl', 3); // Máximo 3 tentativas
};


/**
 * Extrai título e empresa de vaga usando web scraping direto.
 * Não utiliza IA - apenas parsing de HTML (JSON-LD, meta tags, heurísticas).
 * 
 * Estratégia:
 * 1. Web scraping direto para estruturas de dados HTML/JSON-LD
 * 2. Validação rigorosa com scoring (threshold 90%)
 * 3. Falha imediatamente se dados não forem extraídos corretamente
 * 
 * Nota: IA é usada exclusivamente para geração de conteúdo personalizado,
 * não para extração de dados.
 */
export const extractJobTitleAndCompany = async (
  jobContent: string,
  jobUrl?: string
): Promise<{ jobTitle: string; company: string }> => {
  if (!jobContent) {
    throw new Error("Cannot extract details from empty job content.");
  }

  if (!jobUrl) {
    throw new Error(
      "❌ ERRO: URL da vaga não foi fornecida.\n\n" +
      "O sistema agora usa APENAS web scraping direto (sem IA) para extrair título e empresa.\n" +
      "É necessário fornecer a URL da vaga para prosseguir.\n\n" +
      "💡 Dica: Cole a URL da vaga no campo 'Job URL'."
    );
  }

  return withRetry(async (attempt) => {
    try {
      console.log(`🔍 Extraindo título e empresa via web scraping (Tentativa ${attempt}/3)...`);
      const { scrapeJobPosting } = await import('./webScraperService');
      const scrapedData = await scrapeJobPosting(jobUrl);
      
      if (!scrapedData.title || !scrapedData.company) {
        throw new Error(
          `❌ Web scraper não conseguiu extrair título e/ou empresa da página.\n\n` +
          `Extraído: Título="${scrapedData.title || 'N/A'}" | Empresa="${scrapedData.company || 'N/A'}"\n\n` +
          `Possíveis causas:\n` +
          `• Página exige autenticação (login)\n` +
          `• Conteúdo é renderizado por JavaScript (não acessível via HTTP simples)\n` +
          `• Estrutura HTML não possui meta tags ou JSON-LD estruturados\n` +
          `• URL está bloqueada por CORS ou firewall\n\n` +
          `💡 Soluções:\n` +
          `• Tente uma URL diferente da mesma vaga (LinkedIn, Indeed, etc.)\n` +
          `• Cole a descrição da vaga manualmente em vez de usar URL\n` +
          `• Verifique se a URL está acessível publicamente (sem login)`
        );
      }

      const extractedTitle = scrapedData.title.trim();
      const extractedCompany = scrapedData.company.trim();
      
      // Valida os dados extraídos
      const validation = validateAndScoreJobDetails(extractedTitle, extractedCompany);
      
      logExtraction({
        operation: 'extractJobTitleAndCompany-scraper',
        attempt,
        success: validation.isValid,
        confidenceScore: validation.score,
        error: validation.isValid ? undefined : validation.reasons.join('; ')
      });
      
      if (!validation.isValid) {
        const reasonsSummary = validation.reasons.join(' | ');
        throw new Error(
          `❌ VALIDAÇÃO FALHOU (Score: ${validation.score}/100, mínimo: 90)\n\n` +
          `Motivos: ${reasonsSummary}\n\n` +
          `Dados extraídos:\n` +
          `• Título: "${extractedTitle}"\n` +
          `• Empresa: "${extractedCompany}"\n\n` +
          `Os dados não parecem válidos. Não é possível prosseguir com dados incorretos.\n\n` +
          `💡 Soluções:\n` +
          `• Tente outra URL da mesma vaga\n` +
          `• Cole a descrição da vaga manualmente`
        );
      }

      console.log(`✅ Título e empresa extraídos com sucesso! Score: ${validation.score}/100`);
      console.log(`• Título: "${extractedTitle}"`);
      console.log(`• Empresa: "${extractedCompany}"`);
      
      return { jobTitle: extractedTitle, company: extractedCompany };
      
    } catch (error) {
      // Re-lança o erro para o retry handler processar
      throw error;
    }
  }, 'extractJobTitleAndCompany', 3); // Máximo 3 tentativas
};


const parseResponse = (responseText: string): Omit<GeneratedContent, 'sources'> => {
  const sections: { [key: string]: string } = {
    optimizedCv: '### OPTIMIZED CV ###',
    coverLetter: '### COVER LETTER ###',
    networkingMessage: '### NETWORKING MESSAGE ###',
    interviewTips: '### INTERVIEW TIPS ###',
  };

  let remainingText = responseText;
  const parsedContent: any = {};

  const keys = Object.keys(sections);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const startMarker = sections[key];
    const nextKey = i + 1 < keys.length ? keys[i+1] : undefined;
    const endMarker = nextKey ? sections[nextKey] : undefined;
    
    const startIndex = remainingText.indexOf(startMarker);
    if (startIndex === -1) {
      parsedContent[key] = `Error: Could not find section marker ${startMarker}`;
      continue;
    }

    let endIndex = endMarker ? remainingText.indexOf(endMarker, startIndex) : remainingText.length;
    if (endIndex === -1) {
        endIndex = remainingText.length;
    }

    const sectionText = remainingText.substring(startIndex + startMarker.length, endIndex).trim();
    parsedContent[key] = sectionText;
  }

  return {
    optimizedCv: parsedContent.optimizedCv || '',
    coverLetter: parsedContent.coverLetter || '',
    networkingMessage: parsedContent.networkingMessage || '',
    interviewTips: parsedContent.interviewTips || '',
  };
};

export const generateCareerMaterials = async (
  userInput: UserInput,
  jobDetails: JobDetails,
  useThinkingMode: boolean
): Promise<GeneratedContent> => {
  const { cv, tone, language, customContext } = userInput;
  const { jobTitle, company, jobDescription } = jobDetails;

  const modelName = useThinkingMode ? 'gemini-2.5-pro' : 'gemini-2.5-flash';
  
  const config: any = useThinkingMode
    ? { thinkingConfig: { thinkingBudget: 32768 } }
    : {};
  
  // Re-enable Google Search for context enrichment
  config.tools = [{ googleSearch: {} }];

  const prompt = `
    You are an expert career and recruitment AI agent, highly trained in Prompt Engineering and ATS (Applicant Tracking Systems). 
    Your mission is to help a user personalize their career materials for a specific job application using the exact information provided.
    
    **CRITICAL INSTRUCTION: This is the most important rule.** All generated content you produce MUST be for the company **"${company}"** and the role **"${jobTitle}"**. Do NOT mention, suggest, or generate content for any other company or role. Any deviation from this specific company and role is a failure.

    **SAFEGUARD INSTRUCTION:** If the provided Job Title or Company looks generic or incorrect (e.g., "Not found", "N/A", "Company"), you MUST re-analyze the full Job Description provided below to determine the correct Job Title and Company before you begin generating any content. Do not proceed with incorrect information.

    **User's Standard CV:**
    ---
    ${cv}
    ---

    **Target Job:**
    ---
    - Job Title: ${jobTitle}
    - Company: ${company}
    - Job Description: ${jobDescription}
    ---

    **Additional Context & Instructions from User:**
    ---
    - Desired Tone: ${tone}
    - Target Language: ${language}
    - Other Instructions: ${customContext || 'None.'}
    ---

    **Your Task:**
    Analyze all the provided information and use your web search capabilities to research the company and role for additional context. Then, generate the following four items. Remember the critical instruction: all content must be strictly for the **${jobTitle}** role at **${company}**.
    Structure your entire response using the following markdown headers EXACTLY as shown. Do not add any other text before the first header.

    ### OPTIMIZED CV ###
    (Rewrite the user's CV to be perfectly tailored for the job at **${company}**. To ensure it can be formatted correctly, you MUST structure it with the following markdown subheadings:
    
    # [Your Name]
    [Address] | [Phone] | [Email] | [LinkedIn URL]

    ## Summary
    (A 2-3 sentence summary focused on the target role at **${company}**.)
    
    ## Experience
    **[Job Title]** at **[Company Name]** | [City, State]
    *[Start Date] - [End Date]*
    - Responsibility or achievement 1.
    - Responsibility or achievement 2.
    (Repeat for each position)
    
    ## Education
    **[Degree]** at **[Institution]** | [City, State]
    *[Start Date] - [End Date]*

    ## Skills
    - Skill 1, Skill 2, Skill 3
    )

    ### COVER LETTER ###
    (Write a compelling, clear, and direct cover letter for the ${jobTitle} role at **${company}** using the provided job description. Personalize it based on the user's context, CV, and the job description. Address it to the hiring manager at **${company}** if possible.)

    ### NETWORKING MESSAGE ###
    (Create a concise and professional networking message for LinkedIn or email to a recruiter or hiring manager at **${company}** regarding the **${jobTitle}** role, using the provided job description.)

    ### INTERVIEW TIPS ###
    (Provide objective, actionable interview preparation tips specific to the **${jobTitle}** role at **${company}**. Analyze the provided job description for key responsibilities and use your research abilities to find information about the company's culture and interview process. Suggest how the user can prepare to talk about their experience in relation to both the job and the company.)
  `;

  try {
    const promise = ai.models.generateContent({
      model: modelName,
      contents: prompt,
      config,
    });
    const response = await withTimeout(
      promise,
      'Timeout: Content generation took too long.'
    );

    const parsedContent = parseResponse((response as any).text);

    const groundingChunks = (response as any).candidates?.[0]?.groundingMetadata?.groundingChunks || [];
    const sources: GroundingSource[] = groundingChunks
        .filter((chunk: any) => chunk.web && chunk.web.uri)
        .map((chunk: any) => ({
            uri: chunk.web.uri,
            title: chunk.web.title || '',
        }));

    return {
      ...parsedContent,
      sources,
    };
  } catch (error) {
    console.error("Error calling Gemini API:", error);
    if (error instanceof Error) {
        if (error.message.startsWith('Timeout:')) {
            throw error;
        }
        throw new Error(`Failed to generate content: ${error.message}`);
    }
    throw new Error("An unknown error occurred while communicating with the API.");
  }
};