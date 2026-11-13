"""Scraper adapter using Firecrawl API with resilient fallback to high-fidelity BeautifulSoup extraction."""

import logging
import re
from typing import Optional
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScrapedWebpageData(BaseModel):
    """Normalized payload extracted from a target webpage."""
    url: str
    title: str
    description: Optional[str] = None
    main_content: str
    extracted_text: str
    source_type: str = "webpage"  # "product", "article", "landing_page", etc.


class FirecrawlScraperAdapter:
    """Scrapes clean structured webpage markdown via Firecrawl or resilient direct DOM parsing."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "FIRECRAWL_API_KEY", "")

    async def scrape_url(self, url: str) -> ScrapedWebpageData:
        """Fetch URL content cleanly, trying Wikipedia API, Firecrawl, and resilient direct DOM parsing."""
        # 1. High-speed native Wikipedia REST API integration (Zero 403s, instant structured extract)
        if "wikipedia.org/wiki/" in url:
            try:
                wiki_slug = url.split("/wiki/")[-1].split("#")[0].split("?")[0]
                api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        api_url,
                        headers={"User-Agent": "PosterStudio/1.0 (https://42works.com; contact@42works.com)"},
                    )
                    if resp.status_code == 200:
                        wiki_data = resp.json()
                        w_title = wiki_data.get("title") or wiki_slug.replace("_", " ")
                        w_desc = wiki_data.get("description") or f"Historical and cultural landmark: {w_title}"
                        w_extract = wiki_data.get("extract") or ""
                        return ScrapedWebpageData(
                            url=url,
                            title=w_title,
                            description=w_desc,
                            main_content=w_extract,
                            extracted_text=f"{w_title}: {w_extract}",
                            source_type="article",
                        )
            except Exception as w_err:
                logger.warning("Wikipedia API lookup failed, falling back to direct parser: %s", w_err)

        # 2. Try Firecrawl API if key exists
        if self.api_key:
            try:
                app = FirecrawlApp(api_key=self.api_key)
                scrape_res = app.scrape_url(url, params={"formats": ["markdown", "html"]})
                if scrape_res and isinstance(scrape_res, dict):
                    md = scrape_res.get("markdown") or scrape_res.get("content") or ""
                    metadata = scrape_res.get("metadata", {})
                    title = metadata.get("title") or metadata.get("ogTitle") or url
                    desc = metadata.get("description") or metadata.get("ogDescription")
                    return ScrapedWebpageData(
                        url=url,
                        title=title,
                        description=desc,
                        main_content=md[:8000],
                        extracted_text=md[:4000],
                        source_type=self._detect_page_type(url, md),
                    )
            except Exception as err:
                logger.warning("Firecrawl API failed or not reachable, using direct intelligent DOM fallback: %s", err)

        # 3. Resilient Direct DOM Parser (Handles standard web articles, product pages, tech blogs)
        return await self._scrape_direct(url)

    async def _scrape_direct(self, url: str) -> ScrapedWebpageData:
        """High-fidelity direct extraction ignoring navigation, footer, cookies, and ads."""
        headers = {
            "User-Agent": (
                "PosterStudio/1.0 (https://42works.com; contact@42works.com) "
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                res.raise_for_status()
                html_text = res.text
        except Exception as net_err:
            logger.warning("Direct HTTP scrape failed (%s). Extracting semantic topic from URL slug.", net_err)
            path_slug = url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
            return ScrapedWebpageData(
                url=url,
                title=path_slug or "Featured Topic",
                description=f"Information and insights regarding {path_slug}",
                main_content=f"Topic: {path_slug}. Focus on key historical, cultural, and informational significance.",
                extracted_text=f"Topic: {path_slug}. Celebrate the iconic heritage and cultural legacy.",
                source_type="article",
            )

        soup = BeautifulSoup(html_text, "html.parser")

        # Extract Title
        title = ""
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        else:
            title = url

        # Extract Description
        desc = None
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                    soup.find("meta", attrs={"property": re.compile(r"og:description", re.I)})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"].strip()

        # Remove noise elements (scripts, styles, nav, footer, headers, cookie notices)
        for noise in soup.find_all(["script", "style", "nav", "footer", "aside", "noscript", "svg", "form"]):
            noise.decompose()

        # Find main article or body
        main_container = soup.find(["article", "main", 'div[class*="content"]', 'div[class*="post"]', 'div[class*="article"]']) or soup.body

        # Collect informative paragraphs
        paragraphs = []
        if main_container:
            for p in main_container.find_all(["p", "h2", "h3", "li"]):
                txt = p.get_text(strip=True)
                # Keep meaningful content
                if len(txt) > 25:
                    paragraphs.append(txt)

        clean_text = "\n\n".join(paragraphs[:35])  # Cap to top 35 paragraphs
        if not clean_text:
            clean_text = soup.get_text(separator=" ", strip=True)[:4000]

        detected_type = self._detect_page_type(url, clean_text)

        return ScrapedWebpageData(
            url=url,
            title=title,
            description=desc,
            main_content=clean_text[:6000],
            extracted_text=clean_text[:3500],
            source_type=detected_type,
        )

    def _detect_page_type(self, url: str, content: str) -> str:
        """Determines if the page is a product launch, an article/blog, or a corporate service."""
        lower_content = content.lower()
        lower_url = url.lower()

        product_keywords = ["buy now", "add to cart", "price:", "$", "features", "specifications", "pricing", "discount", "pre-order"]
        article_keywords = ["published on", "written by", "read time", "table of contents", "conclusion", "guide", "what you need to know"]

        product_score = sum(1 for kw in product_keywords if kw in lower_content or kw in lower_url)
        article_score = sum(1 for kw in article_keywords if kw in lower_content or kw in lower_url)

        if product_score > article_score and product_score >= 2:
            return "product"
        elif "blog" in lower_url or "article" in lower_url or article_score >= 2:
            return "article"
        return "general"
