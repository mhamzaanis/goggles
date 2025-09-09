import time
import requests
import mysql.connector
from collections import deque
import logging
from bs4 import BeautifulSoup
import re
import json
from typing import List, Tuple, Optional

# ----------------- Logging Setup -----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------- MySQL Setup -----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
    database="search_engine_db"
)
cursor = db.cursor()

# Create table if it doesn't exist
cursor.execute("""
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
    FULLTEXT(title, summary, clean_content)
)
""")

# ----------------- Wikipedia Endpoints -----------------
summary_endpoint = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
content_endpoint = "https://en.wikipedia.org/w/api.php?action=parse&page={}&format=json"
category_members_endpoint = "https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle={}&cmlimit=500&format=json"

# ----------------- Crawler Setup -----------------
visited = set()      # Already fetched articles
queue = deque()      # BFS queue
MAX_ARTICLES = 3000  # Optional limit

# ----------------- Utility Functions -----------------
def clean_html_content(html_content: str) -> str:
    """Extract clean text from HTML content."""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "table", "div.navbox"]):
        script.decompose()
    
    # Get text and clean up
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\[.*?\]', '', text)  # Remove reference numbers
    
    return text

def is_quality_article(title: str, content: str, summary: str) -> bool:
    """Check if article meets quality criteria."""
    # Skip disambiguation pages
    if 'disambiguation' in title.lower() or 'may refer to' in summary.lower():
        return False
    
    # Skip very short articles
    if len(content) < 500:
        return False
    
    # Skip list pages (usually not great for search)
    if title.startswith('List of') or title.startswith('Index of'):
        return False
    
    return True

def retry_request(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Make HTTP request with retry logic."""
    headers = {
        'User-Agent': 'Mini Search Engine Bot/1.0 (Educational Project; Contact: user@example.com)'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None

# ----------------- Functions -----------------
def fetch_article(title):
    """Fetch and save a Wikipedia article, return its linked articles."""
    if title in visited:
        return []

    try:
        # Summary
        summary_resp = retry_request(summary_endpoint.format(title))
        if not summary_resp:
            logger.error(f"Failed to fetch summary for {title}")
            return []
        
        summary_data = summary_resp.json()

        # Full content with links
        content_resp = retry_request(content_endpoint.format(title))
        if not content_resp:
            logger.error(f"Failed to fetch content for {title}")
            return []
        
        content_data = content_resp.json()

        article_title = summary_data.get('title', '')
        summary = summary_data.get('extract', '')
        url = summary_data.get('content_urls', {}).get('desktop', {}).get('page', '')
        content = content_data.get('parse', {}).get('text', {}).get('*', '')
        
        # Clean the HTML content
        clean_content = clean_html_content(content)
        word_count = len(clean_content.split())
        
        # Check quality before saving
        if not is_quality_article(article_title, clean_content, summary):
            logger.info(f"Skipping low-quality article: {article_title}")
            visited.add(title)
            return []

        # Save to MySQL
        try:
            sql = "INSERT INTO wiki_articles (title, summary, content, clean_content, url, word_count) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (article_title, summary, content, clean_content, url, word_count))
            db.commit()
            logger.info(f"[+] Saved article: {article_title} ({word_count} words)")
        except mysql.connector.errors.IntegrityError:
            logger.info(f"[!] Already in DB: {article_title}")

        visited.add(title)

        # Extract links (ns=0 -> main articles)
        links = content_data.get('parse', {}).get('links', [])
        linked_titles = [l['*'] for l in links if l.get('ns') == 0]

        return linked_titles

    except Exception as e:
        logger.error(f"Error fetching {title}: {e}")
        return []

def fetch_category_members(category):
    """Fetch pages and subcategories in a category."""
    try:
        members = []
        url = category_members_endpoint.format(category)
        resp = retry_request(url)
        if not resp:
            logger.error(f"Failed to fetch category {category}")
            return []
        
        data = resp.json()

        for member in data.get('query', {}).get('categorymembers', []):
            members.append((member['title'], member['ns']))  # ns=0 -> page, ns=14 -> subcategory
        return members
    except Exception as e:
        logger.error(f"Error fetching category {category}: {e}")
        return []

def crawl_category(seed_category):
    """Crawl category recursively, including links inside articles."""
    queue.append(seed_category)
    processed_count = 0

    logger.info(f"Starting crawl from: {seed_category}")
    
    while queue and len(visited) < MAX_ARTICLES:
        current = queue.popleft()
        processed_count += 1

        if processed_count % 100 == 0:
            logger.info(f"Progress: {processed_count} processed, {len(visited)} articles saved, {len(queue)} in queue")

        if current.startswith("Category:"):
            # Crawl category members
            logger.info(f"Processing category: {current}")
            members = fetch_category_members(current)
            for title, ns in members:
                if ns == 0:  # Article
                    if title not in visited:
                        queue.append(title)
                elif ns == 14:  # Subcategory
                    if title not in visited:
                        queue.append(title)
        else:
            # Crawl normal article
            new_links = fetch_article(current)
            for link in new_links:
                if link not in visited and len(queue) < 10000:  # Prevent queue from growing too large
                    queue.append(link)

        time.sleep(0.5)  # Respect API rate limit
    
    logger.info(f"Crawling completed. Total articles saved: {len(visited)}")

# ----------------- Search Functions -----------------
def search_articles(query: str, limit: int = 10) -> List[Tuple]:
    """Search articles using MySQL full-text search."""
    try:
        # Full-text search with relevance scoring
        sql = """
        SELECT title, summary, url, word_count,
               MATCH(title, summary, clean_content) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
        FROM wiki_articles 
        WHERE MATCH(title, summary, clean_content) AGAINST(%s IN NATURAL LANGUAGE MODE)
        ORDER BY relevance DESC 
        LIMIT %s
        """
        cursor.execute(sql, (query, query, limit))
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def search_by_title(query: str, limit: int = 10) -> List[Tuple]:
    """Search articles by title similarity."""
    try:
        sql = """
        SELECT title, summary, url, word_count
        FROM wiki_articles 
        WHERE title LIKE %s
        ORDER BY title
        LIMIT %s
        """
        cursor.execute(sql, (f"%{query}%", limit))
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Title search error: {e}")
        return []

def get_article_stats():
    """Get statistics about the crawled articles."""
    try:
        cursor.execute("SELECT COUNT(*) as total, AVG(word_count) as avg_words, MAX(word_count) as max_words FROM wiki_articles")
        stats = cursor.fetchone()
        return {
            'total_articles': stats[0],
            'average_words': round(stats[1], 2) if stats[1] else 0,
            'max_words': stats[2] if stats[2] else 0
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {}

# ----------------- CLI Search Interface -----------------
def interactive_search():
    """Interactive command-line search interface."""
    print("\n" + "="*60)
    print("MINI SEARCH ENGINE - Interactive Search")
    print("="*60)
    
    stats = get_article_stats()
    print(f"Database contains {stats.get('total_articles', 0)} articles")
    print(f"Average article length: {stats.get('average_words', 0)} words")
    print("\nCommands:")
    print("  search <query>     - Full-text search")
    print("  title <query>      - Search by title")
    print("  stats              - Show database statistics")
    print("  quit               - Exit")
    print("-" * 60)
    
    while True:
        try:
            command = input("\nEnter command: ").strip()
            
            if command.lower() == 'quit':
                break
            elif command.lower() == 'stats':
                stats = get_article_stats()
                print(f"\nDatabase Statistics:")
                print(f"Total articles: {stats.get('total_articles', 0)}")
                print(f"Average words per article: {stats.get('average_words', 0)}")
                print(f"Longest article: {stats.get('max_words', 0)} words")
            elif command.startswith('search '):
                query = command[7:].strip()
                if query:
                    results = search_articles(query)
                    print(f"\nFound {len(results)} results for '{query}':")
                    print("-" * 40)
                    for i, (title, summary, url, word_count, relevance) in enumerate(results, 1):
                        print(f"{i}. {title}")
                        print(f"   Words: {word_count} | Relevance: {relevance:.3f}")
                        print(f"   Summary: {summary[:150]}...")
                        print(f"   URL: {url}")
                        print()
            elif command.startswith('title '):
                query = command[6:].strip()
                if query:
                    results = search_by_title(query)
                    print(f"\nFound {len(results)} title matches for '{query}':")
                    print("-" * 40)
                    for i, (title, summary, url, word_count) in enumerate(results, 1):
                        print(f"{i}. {title}")
                        print(f"   Words: {word_count}")
                        print(f"   Summary: {summary[:150]}...")
                        print(f"   URL: {url}")
                        print()
            else:
                print("Unknown command. Use 'search <query>', 'title <query>', 'stats', or 'quit'")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")

# ----------------- Start Crawling -----------------
if __name__ == "__main__":
    try:
        seed_category = "Category:Programming_languages"
        crawl_category(seed_category)
        
        # After crawling, start interactive search
        interactive_search()
        
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        cursor.close()
        db.close()
        logger.info("Database connections closed")