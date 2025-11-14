/**
 * Web Scraper Service - Extração Direta de Vagas via HTTP
 * 
 * Realiza scraping direto de páginas de vagas usando fetch API + parsing HTML.
 * Estratégia dual: tentativa direta + fallback para proxies CORS se necessário.
 */

interface ScrapedJobData {
  title: string;
  company: string;
  description: string;
  fullText: string;
}

interface ScrapeResult {
  success: boolean;
  data?: ScrapedJobData;
  error?: string;
  source: 'direct-scrape' | 'cors-proxy';
}

/**
 * Extrai texto limpo de HTML removendo scripts, styles e tags
 */
const cleanHtmlText = (html: string): string => {
  // Remove scripts e styles
  let cleaned = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  cleaned = cleaned.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
  
  // Remove comentários HTML
  cleaned = cleaned.replace(/<!--[\s\S]*?-->/g, '');
  
  // Substitui tags de quebra por newlines
  cleaned = cleaned.replace(/<br\s*\/?>/gi, '\n');
  cleaned = cleaned.replace(/<\/p>/gi, '\n\n');
  cleaned = cleaned.replace(/<\/div>/gi, '\n');
  cleaned = cleaned.replace(/<\/li>/gi, '\n');
  cleaned = cleaned.replace(/<\/h[1-6]>/gi, '\n\n');
  
  // Remove todas as tags HTML restantes
  cleaned = cleaned.replace(/<[^>]+>/g, ' ');
  
  // Decodifica entidades HTML
  cleaned = cleaned.replace(/&nbsp;/g, ' ');
  cleaned = cleaned.replace(/&amp;/g, '&');
  cleaned = cleaned.replace(/&lt;/g, '<');
  cleaned = cleaned.replace(/&gt;/g, '>');
  cleaned = cleaned.replace(/&quot;/g, '"');
  cleaned = cleaned.replace(/&#39;/g, "'");
  cleaned = cleaned.replace(/&apos;/g, "'");
  
  // Remove múltiplos espaços e quebras de linha
  cleaned = cleaned.replace(/[ \t]+/g, ' ');
  cleaned = cleaned.replace(/\n\s*\n\s*\n/g, '\n\n');
  
  return cleaned.trim();
};

/**
 * Extrai JSON-LD structured data do HTML (comum em sites de vagas)
 */
const extractStructuredData = (html: string): Partial<ScrapedJobData> | null => {
  try {
    // Procura por JSON-LD do tipo JobPosting
    const jsonLdMatch = html.match(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi);
    
    if (jsonLdMatch) {
      for (const scriptTag of jsonLdMatch) {
        const jsonContent = scriptTag.replace(/<script[^>]*>/i, '').replace(/<\/script>/i, '');
        
        try {
          const data = JSON.parse(jsonContent);
          
          // Pode ser array ou objeto único
          const jobPostings = Array.isArray(data) ? data : [data];
          
          for (const item of jobPostings) {
            if (item['@type'] === 'JobPosting') {
              return {
                title: item.title || item.name,
                company: item.hiringOrganization?.name || item.hiringOrganization,
                description: item.description
              };
            }
          }
        } catch (e) {
          // JSON inválido, continua procurando
          continue;
        }
      }
    }
  } catch (error) {
    console.warn('Erro ao extrair structured data:', error);
  }
  
  return null;
};

/**
 * Extrai título da vaga do HTML usando heurísticas
 */
const extractTitle = (html: string, text: string): string => {
  // Tenta meta tags primeiro
  const ogTitleMatch = html.match(/<meta\s+property=["']og:title["']\s+content=["']([^"']+)["']/i);
  if (ogTitleMatch) return ogTitleMatch[1];
  
  const twitterTitleMatch = html.match(/<meta\s+name=["']twitter:title["']\s+content=["']([^"']+)["']/i);
  if (twitterTitleMatch) return twitterTitleMatch[1];
  
  // Tenta <title> tag
  const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
  if (titleMatch) {
    // Remove sufixos comuns como " - LinkedIn", " | Indeed"
    return titleMatch[1].replace(/\s*[-|]\s*(LinkedIn|Indeed|Glassdoor|Monster).*$/i, '').trim();
  }
  
  // Tenta h1
  const h1Match = html.match(/<h1[^>]*>([^<]+)<\/h1>/i);
  if (h1Match) return cleanHtmlText(h1Match[1]);
  
  // Fallback: primeira linha do texto com tamanho razoável
  const lines = text.split('\n').filter(l => l.trim().length > 10 && l.trim().length < 100);
  if (lines.length > 0) return lines[0].trim();
  
  return '';
};

/**
 * Extrai nome da empresa do HTML usando heurísticas
 */
const extractCompany = (html: string, text: string): string => {
  // Tenta structured data primeiro
  const structuredData = extractStructuredData(html);
  if (structuredData?.company) return structuredData.company;
  
  // Tenta padrões comuns em LinkedIn
  const linkedinCompanyMatch = html.match(/<a[^>]*class=["'][^"']*company[^"']*["'][^>]*>([^<]+)<\/a>/i);
  if (linkedinCompanyMatch) return cleanHtmlText(linkedinCompanyMatch[1]);
  
  // Tenta padrões em Indeed
  const indeedCompanyMatch = html.match(/data-company-name=["']([^"']+)["']/i);
  if (indeedCompanyMatch) return indeedCompanyMatch[1];
  
  // Procura por padrões de texto como "Company: X" ou "At X"
  const companyPatterns = [
    /Company:\s*([A-Z][^\n]{2,50})/,
    /Empresa:\s*([A-Z][^\n]{2,50})/,
    /At\s+([A-Z][^\n]{2,50}),/,
    /posted by\s+([A-Z][^\n]{2,50})/i
  ];
  
  for (const pattern of companyPatterns) {
    const match = text.match(pattern);
    if (match) return match[1].trim();
  }
  
  return '';
};

/**
 * Extrai descrição da vaga do HTML
 */
const extractDescription = (html: string, text: string): string => {
  // Tenta structured data primeiro
  const structuredData = extractStructuredData(html);
  if (structuredData?.description) return structuredData.description;
  
  // Tenta encontrar seção de descrição por classes comuns
  const descriptionPatterns = [
    /<div[^>]*class=["'][^"']*description[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<section[^>]*class=["'][^"']*job-description[^"']*["'][^>]*>([\s\S]*?)<\/section>/i,
    /<div[^>]*id=["']job-details["'][^>]*>([\s\S]*?)<\/div>/i
  ];
  
  for (const pattern of descriptionPatterns) {
    const match = html.match(pattern);
    if (match) {
      const cleaned = cleanHtmlText(match[1]);
      if (cleaned.length > 200) return cleaned;
    }
  }
  
  // Fallback: retorna texto completo após limpar
  return text;
};

/**
 * Tenta scrape direto (pode falhar por CORS)
 */
const tryDirectScrape = async (url: string): Promise<ScrapeResult> => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      mode: 'cors',
      cache: 'no-cache'
    });
    
    if (!response.ok) {
      return {
        success: false,
        error: `HTTP ${response.status}: ${response.statusText}`,
        source: 'direct-scrape'
      };
    }
    
    const html = await response.text();
    const text = cleanHtmlText(html);
    
    if (text.length < 100) {
      return {
        success: false,
        error: 'Conteúdo extraído muito curto (possível página de erro)',
        source: 'direct-scrape'
      };
    }
    
    const title = extractTitle(html, text);
    const company = extractCompany(html, text);
    const description = extractDescription(html, text);
    
    return {
      success: true,
      data: {
        title,
        company,
        description,
        fullText: text
      },
      source: 'direct-scrape'
    };
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Erro desconhecido no scraping direto',
      source: 'direct-scrape'
    };
  }
};

/**
 * Tenta scrape via proxy CORS (fallback)
 */
const tryCorsProxyScrape = async (url: string): Promise<ScrapeResult> => {
  const proxies = [
    `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
    `https://corsproxy.io/?${encodeURIComponent(url)}`,
  ];
  
  for (const proxyUrl of proxies) {
    try {
      const response = await fetch(proxyUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
      });
      
      if (!response.ok) continue;
      
      const html = await response.text();
      const text = cleanHtmlText(html);
      
      if (text.length < 100) continue;
      
      const title = extractTitle(html, text);
      const company = extractCompany(html, text);
      const description = extractDescription(html, text);
      
      return {
        success: true,
        data: {
          title,
          company,
          description,
          fullText: text
        },
        source: 'cors-proxy'
      };
      
    } catch (error) {
      // Tenta próximo proxy
      continue;
    }
  }
  
  return {
    success: false,
    error: 'Todos os métodos de scraping falharam (CORS + proxies)',
    source: 'cors-proxy'
  };
};

/**
 * FUNÇÃO PRINCIPAL: Extrai dados de uma vaga de emprego
 * 
 * Estratégia:
 * 1. Tenta scrape direto (mais rápido)
 * 2. Se falhar por CORS, tenta via proxy
 * 3. Valida qualidade dos dados extraídos
 * 4. Retorna resultado estruturado
 */
export const scrapeJobPosting = async (url: string): Promise<ScrapedJobData> => {
  console.log(`[WebScraper] Iniciando extração de: ${url}`);
  
  // Validação básica da URL
  try {
    new URL(url);
  } catch {
    throw new Error(`URL inválida fornecida: "${url}"`);
  }
  
  // Tentativa 1: Scrape direto
  console.log('[WebScraper] Tentativa 1: Scrape direto...');
  let result = await tryDirectScrape(url);
  
  // Tentativa 2: Se falhar, usa proxy CORS
  if (!result.success) {
    console.log(`[WebScraper] Scrape direto falhou: ${result.error}`);
    console.log('[WebScraper] Tentativa 2: Usando CORS proxy...');
    result = await tryCorsProxyScrape(url);
  }
  
  // Se ainda falhou, lança erro
  if (!result.success) {
    throw new Error(
      `Falha ao extrair conteúdo da URL.\n` +
      `Motivo: ${result.error}\n\n` +
      `Possíveis causas:\n` +
      `- Site bloqueia scraping/bots\n` +
      `- CORS está bloqueando acesso\n` +
      `- URL requer autenticação/login\n` +
      `- Página usa JavaScript para renderizar conteúdo\n\n` +
      `Solução: Tente copiar e colar o texto da vaga manualmente.`
    );
  }
  
  const { data } = result;
  
  // Validação de qualidade dos dados extraídos
  if (!data || data.fullText.length < 200) {
    throw new Error(
      `Conteúdo extraído é muito curto (${data?.fullText.length || 0} caracteres).\n` +
      `Possível página de erro ou conteúdo bloqueado.\n` +
      `Por favor, verifique a URL ou cole o texto manualmente.`
    );
  }
  
  console.log(`[WebScraper] ✅ Extração bem-sucedida via ${result.source}`);
  console.log(`[WebScraper] - Título: "${data.title || 'Não extraído'}"`);
  console.log(`[WebScraper] - Empresa: "${data.company || 'Não extraído'}"`);
  console.log(`[WebScraper] - Conteúdo: ${data.fullText.length} caracteres`);
  
  return data;
};

/**
 * Versão simplificada que retorna apenas o texto completo
 * (para compatibilidade com código existente)
 */
export const extractJobContentFromUrl = async (url: string): Promise<string> => {
  const data = await scrapeJobPosting(url);
  return data.fullText;
};

/**
 * Extrai título e empresa diretamente do scraping
 * (sem usar IA, apenas parsing de HTML)
 */
export const extractJobTitleAndCompanyFromScrape = (
  scrapedData: ScrapedJobData
): { jobTitle: string; company: string } => {
  return {
    jobTitle: scrapedData.title || 'Título não identificado',
    company: scrapedData.company || 'Empresa não identificada'
  };
};
