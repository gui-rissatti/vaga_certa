"""
Serviço de web scraping para extração de conteúdo de vagas.
Implementa estratégias múltiplas com fallback automático.
"""
from typing import Dict, Optional
import re
import structlog
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from config import settings

logger = structlog.get_logger()


class WebScraper:
    """
    Serviço de web scraping robusto com múltiplas estratégias de fallback.
    """
    
    def __init__(self, timeout_seconds: int = None):
        """
        Inicializa o web scraper.
        
        Args:
            timeout_seconds: Timeout em segundos (usa config padrão se None)
        """
        self.timeout = timeout_seconds or settings.scraping_timeout_seconds
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def scrape_job_posting(self, url: str) -> Dict[str, str]:
        """
        Extrai dados de uma vaga de emprego.
        
        Args:
            url: URL da vaga
            
        Returns:
            Dicionário com title, company, description e fullText
            
        Raises:
            ValueError: Se scraping falhar
        """
        logger.info("Iniciando scraping", url=url)
        
        # Validação da URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"URL inválida: {url}")
        except Exception as e:
            raise ValueError(f"URL inválida: {url}") from e
        
        # Tentativa 1: Scraping direto
        try:
            result = await self._try_direct_scrape(url)
            if result:
                logger.info("Scraping direto bem-sucedido", url=url)
                return result
        except Exception as e:
            logger.warning("Scraping direto falhou", error=str(e))
        
        # Tentativa 2: Via proxy CORS
        try:
            result = await self._try_cors_proxy_scrape(url)
            if result:
                logger.info("Scraping via proxy bem-sucedido", url=url)
                return result
        except Exception as e:
            logger.warning("Scraping via proxy falhou", error=str(e))
        
        raise ValueError(
            f"Falha ao extrair conteúdo da URL: {url}\n"
            f"Possíveis causas:\n"
            f"- Site bloqueia scraping/bots\n"
            f"- CORS está bloqueando acesso\n"
            f"- URL requer autenticação/login\n"
            f"- Página usa JavaScript para renderizar conteúdo"
        )
    
    async def _try_direct_scrape(self, url: str) -> Optional[Dict[str, str]]:
        """Tenta scraping direto."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            return self._parse_html(html)
        except Exception as e:
            logger.debug("Scraping direto falhou", error=str(e))
            return None
    
    async def _try_cors_proxy_scrape(self, url: str) -> Optional[Dict[str, str]]:
        """Tenta scraping via proxy CORS."""
        proxies = [
            f"https://api.allorigins.win/raw?url={url}",
            f"https://corsproxy.io/?{url}",
        ]
        
        for proxy_url in proxies:
            try:
                response = await self.client.get(proxy_url)
                response.raise_for_status()
                
                html = response.text
                result = self._parse_html(html)
                if result and len(result.get("fullText", "")) > 200:
                    return result
            except Exception:
                continue
        
        return None
    
    def _parse_html(self, html: str) -> Dict[str, str]:
        """
        Parseia HTML e extrai informações da vaga.
        
        Args:
            html: HTML da página
            
        Returns:
            Dicionário com dados extraídos
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Extrai structured data (JSON-LD)
        structured_data = self._extract_structured_data(soup)
        
        # Extrai título
        title = (
            structured_data.get("title")
            or self._extract_title(soup)
            or ""
        )
        
        # Extrai empresa
        company = (
            structured_data.get("company")
            or self._extract_company(soup)
            or ""
        )
        
        # Extrai descrição
        description = (
            structured_data.get("description")
            or self._extract_description(soup)
            or ""
        )
        
        # Texto completo limpo
        full_text = self._extract_full_text(soup)
        
        return {
            "title": title.strip(),
            "company": company.strip(),
            "description": description.strip(),
            "fullText": full_text.strip()
        }
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extrai dados estruturados JSON-LD."""
        result = {}
        
        json_ld_scripts = soup.find_all(
            "script",
            type="application/ld+json"
        )
        
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Pode ser array ou objeto único
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    if item.get("@type") == "JobPosting":
                        result["title"] = item.get("title") or item.get("name", "")
                        org = item.get("hiringOrganization", {})
                        if isinstance(org, dict):
                            result["company"] = org.get("name", "")
                        else:
                            result["company"] = str(org)
                        result["description"] = item.get("description", "")
                        break
            except Exception:
                continue
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai título usando heurísticas."""
        # Meta tags
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter_title:
            return twitter_title.get("content", "")
        
        # Tag title
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.string or ""
            # Remove sufixos comuns
            title = re.sub(r"\s*[-|]\s*(LinkedIn|Indeed|Glassdoor).*$", "", title, flags=re.IGNORECASE)
            return title.strip()
        
        # H1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extrai nome da empresa usando heurísticas."""
        # Padrões comuns em sites de vagas
        patterns = [
            soup.find("a", class_=re.compile(r"company", re.I)),
            soup.find(attrs={"data-company-name": True}),
        ]
        
        for element in patterns:
            if element:
                if element.name == "a":
                    return element.get_text(strip=True)
                else:
                    return element.get("data-company-name", "")
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrai descrição da vaga."""
        # Procura por seções de descrição
        description_selectors = [
            soup.find("div", class_=re.compile(r"description", re.I)),
            soup.find("section", class_=re.compile(r"job-description", re.I)),
            soup.find("div", id=re.compile(r"job-details", re.I)),
        ]
        
        for element in description_selectors:
            if element:
                text = element.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    return text
        
        return ""
    
    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extrai texto completo limpo da página."""
        # Remove scripts e styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        # Extrai texto
        text = soup.get_text(separator="\n", strip=True)
        
        # Limpa espaços múltiplos e quebras de linha
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = re.sub(r" +", " ", text)
        
        return text.strip()
    
    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()

