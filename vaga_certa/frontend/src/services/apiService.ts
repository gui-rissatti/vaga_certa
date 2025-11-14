/**
 * Serviço de API para comunicação com o backend Python.
 * Substitui o uso direto do Gemini SDK por chamadas REST à API FastAPI.
 */

import type { UserInput, GeneratedContent, JobDetails } from '../types';

// URL base da API (configurável via variável de ambiente)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiError {
  error: string;
  detail?: string;
  error_code?: string;
}

/**
 * Cliente HTTP com tratamento de erros padronizado e mensagens humanizadas
 * BUG FIX: Converte objetos de erro em strings leg\u00edveis para evitar "[object Object]"
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = 'Erro na requisição';
      
      try {
        const errorData: ApiError = await response.json();
        
        // BUG FIX: Extrai mensagem de erro de forma mais robusta
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else {
          errorMessage = `Erro HTTP ${response.status}: ${response.statusText}`;
        }
        
        // Se for erro de validação (422), torna mensagem mais amigável
        if (response.status === 422) {
          errorMessage = `❌ Dados inválidos: ${errorMessage}`;
        }
      } catch (parseError) {
        // Se não conseguir parsear JSON, usa mensagem genérica
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    // BUG FIX: Garante que sempre retornamos uma mensagem de erro como string
    if (error instanceof Error) {
      throw error;
    }
    
    // Se for outro tipo de erro (ex: TypeError de rede), converte para string
    const errorMsg = typeof error === 'object' && error !== null
      ? JSON.stringify(error)
      : String(error);
    
    throw new Error(`Erro de rede: ${errorMsg}`);
  }
}

/**
 * Extrai conteúdo da vaga a partir da URL.
 * Usa o endpoint de extração do backend Python.
 */
export async function extractJobContentFromUrl(jobUrl: string): Promise<string> {
  try {
    const result = await apiRequest<{
      job_title: string;
      company: string;
      job_description: string;
      validation: any;
      source: string;
      content_score?: number;
    }>('/extract-job-details', {
      method: 'POST',
      body: JSON.stringify({ job_url: jobUrl }),
    });

    return result.job_description;
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? error.message
        : 'Falha ao extrair conteúdo da vaga'
    );
  }
}

/**
 * Extrai título e empresa da vaga.
 * Usa o endpoint de extração do backend Python.
 */
export async function extractJobTitleAndCompany(
  jobContent: string,
  jobUrl?: string
): Promise<{ jobTitle: string; company: string; contentScore?: number; validationWarning?: string }> {
  if (!jobUrl) {
    throw new Error(
      'URL da vaga é obrigatória para extração via API Python'
    );
  }

  try {
    const result = await apiRequest<{
      job_title: string;
      company: string;
      job_description: string;
      validation: any;
      source: string;
      content_score?: number;
    }>('/extract-job-details', {
      method: 'POST',
      body: JSON.stringify({ job_url: jobUrl }),
    });

    const contentScore = result.content_score;
    let validationWarning: string | undefined = undefined;

    // Score entre 30-70: warning para o usuário
    if (contentScore !== undefined && contentScore >= 30 && contentScore < 70) {
      const validation = result.validation?.content;
      const reasons = validation?.reasons ? validation.reasons.join(', ') : 'Detalhes limitados';
      validationWarning = `Atenção: Esta vaga possui poucos detalhes (Score: ${contentScore}/100). ` +
        `Os materiais gerados podem ser menos precisos. Motivo: ${reasons}`;
    }

    return {
      jobTitle: result.job_title,
      company: result.company,
      contentScore,
      validationWarning,
    };
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? error.message
        : 'Falha ao extrair título e empresa'
    );
  }
}

/**
 * Gera materiais de carreira personalizados.
 * Usa o endpoint de geração do backend Python.
 */
export async function generateCareerMaterials(
  userInput: UserInput,
  jobDetails: JobDetails,
  useThinkingMode: boolean = false
): Promise<GeneratedContent> {
  const { cv, tone, language, customContext } = userInput;
  const { jobTitle, company, jobDescription } = jobDetails;

  try {
    const result = await apiRequest<{
      optimized_cv: string;
      cover_letter: string;
      networking_message: string;
      interview_tips: string;
      sources: Array<{ uri: string; title: string }>;
      compatibility?: {
        score: number;
        label: string;
        strengths: string[];
        gaps: string[];
        coverage_ratio: number;
      };
      metadata: any;
    }>('/generate-materials', {
      method: 'POST',
      body: JSON.stringify({
        cv,
        job_title: jobTitle,
        company,
        job_description: jobDescription,
        tone,
        language,
        custom_context: customContext || '',
        use_thinking_mode: useThinkingMode,
      }),
    });

    return {
      optimizedCv: result.optimized_cv,
      coverLetter: result.cover_letter,
      networkingMessage: result.networking_message,
      interviewTips: result.interview_tips,
      sources: result.sources.map(s => ({
        uri: s.uri,
        title: s.title,
      })),
      compatibility: result.compatibility
        ? {
            score: result.compatibility.score,
            label: result.compatibility.label,
            strengths: result.compatibility.strengths ?? [],
            gaps: result.compatibility.gaps ?? [],
            coverageRatio: result.compatibility.coverage_ratio ?? 0,
          }
        : undefined,
    };
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? error.message
        : 'Falha ao gerar materiais de carreira'
    );
  }
}

/**
 * Endpoint completo que extrai detalhes e gera materiais em uma única chamada.
 * Útil para simplificar o fluxo no frontend.
 */
export async function generateComplete(
  userInput: UserInput
): Promise<{
  jobDetails: JobDetails;
  materials: GeneratedContent;
}> {
  try {
    const result = await apiRequest<{
      jobDetails: {
        jobTitle: string;
        company: string;
        jobDescription: string;
        validation: any;
      };
      materials: {
        optimized_cv: string;
        cover_letter: string;
        networking_message: string;
        interview_tips: string;
        sources: Array<{ uri: string; title: string }>;
        compatibility?: {
          score: number;
          label: string;
          strengths: string[];
          gaps: string[];
          coverage_ratio: number;
        };
        metadata: any;
      };
    }>('/generate-complete', {
      method: 'POST',
      body: JSON.stringify({
        cv: userInput.cv,
        job_url: userInput.jobUrl,
        tone: userInput.tone,
        language: userInput.language,
        custom_context: userInput.customContext || '',
      }),
    });

    return {
      jobDetails: {
        jobTitle: result.jobDetails.jobTitle,
        company: result.jobDetails.company,
        jobDescription: result.jobDetails.jobDescription,
      },
      materials: {
        optimizedCv: result.materials.optimized_cv,
        coverLetter: result.materials.cover_letter,
        networkingMessage: result.materials.networking_message,
        interviewTips: result.materials.interview_tips,
        sources: result.materials.sources.map(s => ({
          uri: s.uri,
          title: s.title,
        })),
        compatibility: result.materials.compatibility
          ? {
              score: result.materials.compatibility.score,
              label: result.materials.compatibility.label,
              strengths: result.materials.compatibility.strengths ?? [],
              gaps: result.materials.compatibility.gaps ?? [],
              coverageRatio: result.materials.compatibility.coverage_ratio ?? 0,
            }
          : undefined,
      },
    };
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? error.message
        : 'Falha no processamento completo'
    );
  }
}

/**
 * Health check da API
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const result = await apiRequest<{ status: string }>('/health');
    return result.status === 'healthy';
  } catch {
    return false;
  }
}
