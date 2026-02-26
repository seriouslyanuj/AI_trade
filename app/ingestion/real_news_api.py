import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)

class RealNewsAPIClient:
    """Real news API integrations - NewsAPI, Alpha Vantage, GNews"""
    
    def __init__(self):
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")
        self.gnews_key = os.getenv("GNEWS_API_KEY")
        
        # Indian financial news keywords
        self.keywords = [
            "NSE", "BSE", "Sensex", "Nifty", "stock market",
            "earnings", "quarterly results", "merger", "acquisition"
        ]
        
        # NSE Top 50 symbols
        self.symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE",
            "ASIANPAINT", "MARUTI", "HCLTECH", "KOTAKBANK", "LT",
            "AXISBANK", "WIPRO", "TITAN", "ULTRACEMCO", "SUNPHARMA"
        ]
    
    async def fetch_newsapi(self, query: str = "India stocks") -> List[Dict]:
        """Fetch from NewsAPI.org"""
        if not self.newsapi_key or self.newsapi_key == "your_newsapi_key_here":
            logger.warning("NewsAPI key not configured")
            return []
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.newsapi_key,
            "pageSize": 20
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        
                        for article in data.get("articles", []):
                            # Extract mentioned symbols
                            title_body = f"{article.get('title', '')} {article.get('description', '')}"
                            symbols = self._extract_symbols(title_body)
                            
                            articles.append({
                                "id": f"newsapi_{article.get('publishedAt', '')}",
                                "timestamp": article.get("publishedAt"),
                                "title": article.get("title", ""),
                                "body": article.get("description", ""),
                                "source": "newsapi",
                                "url": article.get("url"),
                                "symbols": symbols
                            })
                        
                        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                        return articles
                    else:
                        logger.error(f"NewsAPI error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"NewsAPI fetch failed: {e}")
            return []
    
    async def fetch_alpha_vantage_news(self, tickers: str = "NSE:RELIANCE") -> List[Dict]:
        """Fetch from Alpha Vantage News & Sentiments"""
        if not self.alpha_vantage_key or self.alpha_vantage_key == "your_alphavantage_key_here":
            logger.warning("Alpha Vantage key not configured")
            return []
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": tickers,
            "apikey": self.alpha_vantage_key,
            "limit": 50
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        
                        for item in data.get("feed", []):
                            # Get ticker sentiments
                            ticker_sentiment = item.get("ticker_sentiment", [])
                            symbols = [ts.get("ticker", "").replace("NSE:", "") 
                                     for ts in ticker_sentiment]
                            
                            articles.append({
                                "id": f"alpha_{item.get('time_published', '')}",
                                "timestamp": self._parse_alpha_time(item.get("time_published")),
                                "title": item.get("title", ""),
                                "body": item.get("summary", ""),
                                "source": "alpha_vantage",
                                "url": item.get("url"),
                                "symbols": symbols,
                                "sentiment_score": item.get("overall_sentiment_score", 0)
                            })
                        
                        logger.info(f"Fetched {len(articles)} articles from Alpha Vantage")
                        return articles
                    else:
                        logger.error(f"Alpha Vantage error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Alpha Vantage fetch failed: {e}")
            return []
    
    async def fetch_gnews(self, query: str = "India stock market") -> List[Dict]:
        """Fetch from GNews API"""
        if not self.gnews_key or self.gnews_key == "your_gnews_key_here":
            logger.warning("GNews key not configured")
            return []
        
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "country": "in",
            "max": 20,
            "apikey": self.gnews_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        
                        for article in data.get("articles", []):
                            title_body = f"{article.get('title', '')} {article.get('description', '')}"
                            symbols = self._extract_symbols(title_body)
                            
                            articles.append({
                                "id": f"gnews_{article.get('publishedAt', '')}",
                                "timestamp": article.get("publishedAt"),
                                "title": article.get("title", ""),
                                "body": article.get("description", ""),
                                "source": "gnews",
                                "url": article.get("url"),
                                "symbols": symbols
                            })
                        
                        logger.info(f"Fetched {len(articles)} articles from GNews")
                        return articles
                    else:
                        logger.error(f"GNews error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"GNews fetch failed: {e}")
            return []
    
    async def fetch_all_news(self) -> List[Dict]:
        """Aggregate news from all sources"""
        tasks = [
            self.fetch_newsapi("India stocks NSE BSE"),
            self.fetch_alpha_vantage_news("NSE:RELIANCE,NSE:TCS,NSE:INFY"),
            self.fetch_gnews("India stock market earnings")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Deduplicate by title similarity
        unique_articles = self._deduplicate(all_articles)
        
        logger.info(f"Total unique articles: {len(unique_articles)}")
        return unique_articles
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        text_upper = text.upper()
        found = []
        
        for symbol in self.symbols:
            if symbol in text_upper:
                found.append(symbol)
        
        return found if found else ["NIFTY50"]
    
    def _parse_alpha_time(self, time_str: str) -> str:
        """Parse Alpha Vantage time format (YYYYMMDDTHHMMSS) to ISO"""
        try:
            if len(time_str) == 15:  # YYYYMMDDTHHMMSS
                dt = datetime.strptime(time_str, "%Y%m%dT%H%M%S")
                return dt.isoformat()
        except:
            pass
        return datetime.now().isoformat()
    
    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles by title similarity"""
        seen_titles = set()
        unique = []
        
        for article in articles:
            title = article.get("title", "").lower()
            # Simple dedup - could use fuzzy matching
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique.append(article)
        
        return unique
