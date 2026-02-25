import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set
import feedparser
import aiohttp
from bs4 import BeautifulSoup

class RSSNewsIngestion:
    """Real-time news ingestion from RSS feeds"""
    
    # Indian financial news RSS feeds
    FEEDS = [
        "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "https://www.moneycontrol.com/rss/latestnews.xml",
        "https://www.livemint.com/rss/markets",
        "https://www.business-standard.com/rss/markets-106.rss",
    ]
    
    # NSE Top 50 stocks
    TRACKED_SYMBOLS = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", "ASIANPAINT", "MARUTI",
        "HCLTECH", "KOTAKBANK", "LT", "AXISBANK", "WIPRO", "TITAN",
        "ULTRACEMCO", "SUNPHARMA", "NESTLEIND", "TATASTEEL", "BAJAJFINSV",
        "TECHM", "POWERGRID", "NTPC", "ONGC", "ADANIPORTS", "COALINDIA"
    ]
    
    def __init__(self, callback=None):
        self.callback = callback
        self.seen_articles: Set[str] = set()  # Deduplication
        self.is_running = False
        
    def _hash_article(self, title: str, link: str) -> str:
        """Generate unique hash for article"""
        return hashlib.md5(f"{title}{link}".encode()).hexdigest()
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract mentioned stock symbols from text"""
        text_upper = text.upper()
        mentioned = []
        
        for symbol in self.TRACKED_SYMBOLS:
            if symbol in text_upper:
                mentioned.append(symbol)
        
        # Also check company names (simplified)
        name_map = {
            "RELIANCE": ["RELIANCE", "RIL"],
            "TCS": ["TATA CONSULTANCY", "TCS"],
            "INFY": ["INFOSYS"],
            "HDFCBANK": ["HDFC BANK"],
            "ITC": ["ITC LIMITED"],
        }
        
        for symbol, names in name_map.items():
            for name in names:
                if name in text_upper and symbol not in mentioned:
                    mentioned.append(symbol)
                    break
        
        return mentioned if mentioned else ["NIFTY50"]  # Default index
    
    async def fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=10) as response:
                    content = await response.text()
            
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries[:10]:  # Latest 10 articles
                article_hash = self._hash_article(entry.title, entry.link)
                
                # Skip if already seen
                if article_hash in self.seen_articles:
                    continue
                
                self.seen_articles.add(article_hash)
                
                # Extract symbols
                full_text = f"{entry.title} {entry.get('summary', '')}"
                symbols = self._extract_symbols(full_text)
                
                article = {
                    'id': article_hash,
                    'timestamp': datetime.now().isoformat(),
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', '')[:500],
                    'source': feed_url,
                    'symbols': symbols,
                    'published': entry.get('published', datetime.now().isoformat())
                }
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []
    
    async def stream_news(self, interval_seconds: int = 60):
        """Continuous news streaming loop"""
        self.is_running = True
        print(f"📡 Starting news ingestion from {len(self.FEEDS)} feeds...")
        
        while self.is_running:
            all_articles = []
            
            # Fetch from all feeds concurrently
            tasks = [self.fetch_feed(feed) for feed in self.FEEDS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for articles in results:
                if isinstance(articles, list):
                    all_articles.extend(articles)
            
            # Process new articles
            if all_articles:
                print(f"✅ Fetched {len(all_articles)} new articles")
                
                # Call callback for each article
                if self.callback:
                    for article in all_articles:
                        try:
                            await self.callback(article)
                        except Exception as e:
                            print(f"Error in callback: {e}")
            
            # Wait before next fetch
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop news streaming"""
        self.is_running = False
        print("🛑 Stopped news ingestion")
    
    async def get_latest_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get latest news for specific symbol (mock implementation)"""
        # In production, query from database
        return [{
            'symbol': symbol,
            'title': f"Sample news for {symbol}",
            'sentiment': 0.5,
            'timestamp': datetime.now().isoformat()
        }]
