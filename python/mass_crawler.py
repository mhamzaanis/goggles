#!/usr/bin/env python3
"""
Optimized Mass Wikipedia Crawler for Mini Search Engine
This crawler is designed to efficiently collect thousands of articles
"""

import time
import requests
import mysql.connector
from collections import deque
import logging
from bs4 import BeautifulSoup
import re
from typing import List, Tuple, Optional
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

# ----------------- Logging Setup -----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mass_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------- Configuration -----------------
MAX_ARTICLES = 10000  # Target number of articles
MAX_WORKERS = 5       # Number of concurrent threads
BATCH_SIZE = 100      # Database batch insert size
RATE_LIMIT = 0.2      # Seconds between requests per thread

# Headers for Wikipedia API
HEADERS = {
    'User-Agent': 'Mini Search Engine Bot/1.0 (Educational Project; Contact: user@example.com)'
}

# Starting categories with high-quality articles
SEED_CATEGORIES = [
    "Category:Programming_languages",
    "Category:Computer_science",
    "Category:Technology",
    "Category:Science",
    "Category:Mathematics",
    "Category:Physics",
    "Category:Chemistry",
    "Category:Biology",
    "Category:History",
    "Category:Geography"
]

class MassCrawler:
    def __init__(self):
        # Try to import config, fall back to defaults if not available
        try:
            from config import DB_CONFIG
            db_config = DB_CONFIG
        except ImportError:
            # Default configuration - update these for production!
            db_config = {
                'host': "localhost",
                'user': "root",
                'password': "admin",  # CHANGE THIS!
                'database': "search_engine_db"
            }
            print("⚠️  Using default database credentials. Please create config.py for production!")
        
        self.db = mysql.connector.connect(
            **db_config,
            autocommit=False
        )
        self.cursor = self.db.cursor()
        self.setup_database()
        
        self.visited = set()
        self.queue = deque()
        self.article_batch = []
        self.lock = threading.Lock()
        
        # Load existing articles to avoid duplicates
        self.load_existing_articles()
    
    def setup_database(self):
        """Create optimized database table."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS wiki_articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) UNIQUE,
            summary TEXT,
            content LONGTEXT,
            clean_content LONGTEXT,
            url VARCHAR(500),
            word_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_title (title),
            INDEX idx_word_count (word_count),
            INDEX idx_created (created_at),
            FULLTEXT(title, summary, clean_content)
        )
        """)
        self.db.commit()
    
    def load_existing_articles(self):
        """Load existing article titles to avoid duplicates."""
        self.cursor.execute("SELECT title FROM wiki_articles")
        existing = self.cursor.fetchall()
        self.visited.update(row[0] for row in existing)
        logger.info(f"Loaded {len(self.visited)} existing articles")
    
    def cleanup(self):
        """Cleanup database connections and resources."""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'db') and self.db:
                self.db.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def clean_html_content(self, html_content: str) -> str:
        """Extract clean text from HTML content."""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "table", "div.navbox", "div.infobox"]):
                element.decompose()
            
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[.*?\]', '', text)  # Remove reference numbers
            
            # Sanitize for database - remove or escape problematic characters
            text = text.replace('\x00', '')  # Remove null bytes
            text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)  # Remove control characters
            
            return text
        except Exception as e:
            logger.warning(f"Error cleaning HTML content: {e}")
            return ""
    
    def is_quality_article(self, title: str, content: str, summary: str) -> bool:
        """Enhanced quality filtering."""
        # Skip disambiguation and list pages
        skip_patterns = [
            'disambiguation', 'may refer to', 'list of', 'index of',
            'category:', 'template:', 'file:', 'portal:'
        ]
        
        title_lower = title.lower()
        summary_lower = summary.lower()
        
        for pattern in skip_patterns:
            if pattern in title_lower or pattern in summary_lower:
                return False
        
        # Require minimum content length
        if len(content) < 1000:
            return False
        
        # Require meaningful summary
        if len(summary) < 100:
            return False
        
        return True
    
    def fetch_article(self, title: str) -> Optional[dict]:
        """Fetch a single article with optimized error handling."""
        if title in self.visited:
            return None
        
        try:
            # Summary endpoint
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            summary_resp = requests.get(summary_url, headers=HEADERS, timeout=10)
            
            if summary_resp.status_code != 200:
                return None
            
            summary_data = summary_resp.json()
            
            # Content endpoint
            content_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&format=json"
            content_resp = requests.get(content_url, headers=HEADERS, timeout=10)
            
            if content_resp.status_code != 200:
                return None
            
            content_data = content_resp.json()
            
            # Extract data
            article_title = summary_data.get('title', '')
            summary = summary_data.get('extract', '')
            url = summary_data.get('content_urls', {}).get('desktop', {}).get('page', '')
            content = content_data.get('parse', {}).get('text', {}).get('*', '')
            
            # Quality check
            if not self.is_quality_article(article_title, content, summary):
                return None
            
            # Clean content
            clean_content = self.clean_html_content(content)
            word_count = len(clean_content.split())
            
            # Extract links for further crawling
            links = content_data.get('parse', {}).get('links', [])
            linked_titles = [l['*'] for l in links if l.get('ns') == 0]
            
            return {
                'title': article_title,
                'summary': summary,
                'content': content,
                'clean_content': clean_content,
                'url': url,
                'word_count': word_count,
                'links': linked_titles
            }
            
        except Exception as e:
            logger.warning(f"Error fetching {title}: {e}")
            return None
    
    def fetch_category_members(self, category: str) -> List[Tuple[str, int]]:
        """Fetch category members with pagination."""
        try:
            members = []
            continue_param = None
            
            while len(members) < 500:  # Limit per category
                url = f"https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle={category}&cmlimit=500&format=json"
                if continue_param:
                    url += f"&cmcontinue={continue_param}"
                
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    break
                
                data = resp.json()
                category_members = data.get('query', {}).get('categorymembers', [])
                
                for member in category_members:
                    members.append((member['title'], member['ns']))
                
                # Check for continuation
                continue_param = data.get('continue', {}).get('cmcontinue')
                if not continue_param:
                    break
            
            return members
            
        except Exception as e:
            logger.error(f"Error fetching category {category}: {e}")
            return []
    
    def batch_insert_articles(self, articles: List[dict]):
        """Insert articles in batches for better performance."""
        if not articles:
            return
        
        try:
            sql = """
            INSERT IGNORE INTO wiki_articles 
            (title, summary, content, clean_content, url, word_count) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # Sanitize all text fields before insertion
            values = []
            for a in articles:
                try:
                    # Ensure all text fields are properly encoded and sanitized
                    title = str(a['title'])[:255] if a['title'] else ""
                    summary = str(a['summary']) if a['summary'] else ""
                    content = str(a['content']) if a['content'] else ""
                    clean_content = str(a['clean_content']) if a['clean_content'] else ""
                    url = str(a['url'])[:500] if a['url'] else ""
                    word_count = int(a['word_count']) if a['word_count'] else 0
                    
                    values.append((title, summary, content, clean_content, url, word_count))
                except Exception as e:
                    logger.warning(f"Error processing article {a.get('title', 'Unknown')}: {e}")
                    continue
            
            if values:
                self.cursor.executemany(sql, values)
                self.db.commit()
                logger.info(f"Batch inserted {len(values)} articles")
            
        except Exception as e:
            logger.error(f"Batch insert error: {e}")
            self.db.rollback()
    
    def worker_thread(self, thread_id: int):
        """Worker thread for concurrent crawling."""
        logger.info(f"Worker {thread_id} started")
        articles_processed = 0
        
        while len(self.visited) < MAX_ARTICLES:
            with self.lock:
                if not self.queue:
                    break
                current = self.queue.popleft()
            
            if current in self.visited:
                continue
            
            # Fetch article
            article_data = self.fetch_article(current)
            
            with self.lock:
                self.visited.add(current)
                
                if article_data:
                    self.article_batch.append(article_data)
                    articles_processed += 1
                    
                    # Add new links to queue
                    for link in article_data['links'][:10]:  # Limit links per article
                        if link not in self.visited and len(self.queue) < 50000:
                            self.queue.append(link)
                    
                    # Batch insert when ready
                    if len(self.article_batch) >= BATCH_SIZE:
                        self.batch_insert_articles(self.article_batch)
                        self.article_batch.clear()
            
            # Rate limiting
            time.sleep(RATE_LIMIT)
            
            if articles_processed % 50 == 0 and articles_processed > 0:
                logger.info(f"Worker {thread_id}: {articles_processed} articles processed")
        
        logger.info(f"Worker {thread_id} finished. Processed {articles_processed} articles")
    
    def populate_initial_queue(self):
        """Populate queue with articles from seed categories."""
        logger.info("Populating initial queue from seed categories...")
        
        for category in SEED_CATEGORIES:
            members = self.fetch_category_members(category)
            logger.info(f"Found {len(members)} members in {category}")
            
            for title, ns in members:
                if ns == 0 and title not in self.visited:  # Articles only
                    self.queue.append(title)
                elif ns == 14:  # Subcategories
                    sub_members = self.fetch_category_members(title)
                    for sub_title, sub_ns in sub_members[:50]:  # Limit subcategory expansion
                        if sub_ns == 0 and sub_title not in self.visited:
                            self.queue.append(sub_title)
            
            time.sleep(1)  # Rate limit between categories
        
        logger.info(f"Initial queue populated with {len(self.queue)} articles")
    
    def run(self):
        """Run the mass crawler with multiple threads."""
        logger.info(f"Starting mass crawler - Target: {MAX_ARTICLES} articles")
        
        # Populate initial queue
        self.populate_initial_queue()
        
        if not self.queue:
            logger.error("No articles in queue. Cannot start crawling.")
            return
        
        # Start worker threads
        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [
                    executor.submit(self.worker_thread, i) 
                    for i in range(MAX_WORKERS)
                ]
                
                # Monitor progress
                start_time = time.time()
                while any(not f.done() for f in futures):
                    time.sleep(30)  # Progress update every 30 seconds
                    
                    with self.lock:
                        current_count = len(self.visited)
                        queue_size = len(self.queue)
                        elapsed = time.time() - start_time
                        rate = current_count / elapsed if elapsed > 0 else 0
                    
                    logger.info(f"Progress: {current_count}/{MAX_ARTICLES} articles, {queue_size} queued, {rate:.2f} articles/sec")
                    
                    if current_count >= MAX_ARTICLES:
                        logger.info("Target reached! Stopping threads...")
                        break
        except KeyboardInterrupt:
            logger.info("Crawling interrupted - cleaning up threads...")
            # The ThreadPoolExecutor context manager will handle thread cleanup
            raise
        
        # Final batch insert
        if self.article_batch:
            self.batch_insert_articles(self.article_batch)
        
        # Final stats
        self.cursor.execute("SELECT COUNT(*) FROM wiki_articles")
        total_articles = self.cursor.fetchone()[0]
        
        elapsed = time.time() - start_time
        logger.info(f"Crawling completed!")
        logger.info(f"Total articles in database: {total_articles}")
        logger.info(f"Time elapsed: {elapsed:.2f} seconds")
        logger.info(f"Average rate: {total_articles/elapsed:.2f} articles/sec")

def main():
    """Main function to run the mass crawler."""
    crawler = None
    try:
        crawler = MassCrawler()
        crawler.run()
        
        print(f"\n🎉 Mass crawling completed!")
        print(f"Your search engine now has tons of articles!")
        print(f"\nNext steps:")
        print(f"1. Start web interface: python web_search.py")
        print(f"2. Build advanced search: python advanced_search.py")
        
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Ensure database connections are closed
        if crawler:
            crawler.cleanup()
        logger.info("Crawler shutdown complete")

if __name__ == "__main__":
    main()
