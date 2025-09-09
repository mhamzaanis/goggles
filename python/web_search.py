from flask import Flask, render_template, request, jsonify
import mysql.connector
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="search_engine_db"
    )

class SearchEngine:
    def __init__(self):
        self.db = get_db_connection()
        self.cursor = self.db.cursor()
    
    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search articles using MySQL full-text search."""
        try:
            sql = """
            SELECT title, summary, url, word_count,
                   MATCH(title, summary, clean_content) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
            FROM wiki_articles 
            WHERE MATCH(title, summary, clean_content) AGAINST(%s IN NATURAL LANGUAGE MODE)
            ORDER BY relevance DESC 
            LIMIT %s
            """
            self.cursor.execute(sql, (query, query, limit))
            results = self.cursor.fetchall()
            
            return [
                {
                    'title': row[0],
                    'summary': row[1],
                    'url': row[2],
                    'word_count': row[3],
                    'relevance': float(row[4])
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_by_title(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search articles by title similarity."""
        try:
            sql = """
            SELECT title, summary, url, word_count
            FROM wiki_articles 
            WHERE title LIKE %s
            ORDER BY 
                CASE 
                    WHEN title = %s THEN 1
                    WHEN title LIKE %s THEN 2
                    ELSE 3
                END,
                title
            LIMIT %s
            """
            like_query = f"%{query}%"
            starts_query = f"{query}%"
            self.cursor.execute(sql, (like_query, query, starts_query, limit))
            results = self.cursor.fetchall()
            
            return [
                {
                    'title': row[0],
                    'summary': row[1],
                    'url': row[2],
                    'word_count': row[3],
                    'relevance': 1.0  # Default relevance for title search
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Title search error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(word_count) as avg_words,
                    MAX(word_count) as max_words,
                    MIN(word_count) as min_words
                FROM wiki_articles
            """)
            stats = self.cursor.fetchone()
            
            return {
                'total_articles': stats[0],
                'avg_words': round(stats[1], 2) if stats[1] else 0,
                'max_words': stats[2] if stats[2] else 0,
                'min_words': stats[3] if stats[3] else 0
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added articles."""
        try:
            sql = """
            SELECT title, summary, url, word_count, created_at
            FROM wiki_articles 
            ORDER BY created_at DESC
            LIMIT %s
            """
            self.cursor.execute(sql, (limit,))
            results = self.cursor.fetchall()
            
            return [
                {
                    'title': row[0],
                    'summary': row[1],
                    'url': row[2],
                    'word_count': row[3],
                    'created_at': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else 'Unknown'
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Recent articles error: {e}")
            return []

# Initialize search engine
search_engine = SearchEngine()

@app.route('/')
def index():
    """Main search page."""
    stats = search_engine.get_stats()
    recent_articles = search_engine.get_recent_articles(5)
    return render_template('index.html', stats=stats, recent_articles=recent_articles)

@app.route('/search')
def search():
    """Handle search requests."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'content')  # 'content' or 'title'
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    if search_type == 'title':
        results = search_engine.search_by_title(query)
    else:
        results = search_engine.search_articles(query)
    
    return jsonify({
        'query': query,
        'type': search_type,
        'results': results,
        'count': len(results)
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    return jsonify(search_engine.get_stats())

@app.route('/api/recent')
def api_recent():
    """API endpoint for recent articles."""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(search_engine.get_recent_articles(limit))

if __name__ == '__main__':
    print("Starting Mini Search Engine Web Interface...")
    print("Visit http://localhost:5000 to access the search interface")
    app.run(debug=True, host='0.0.0.0', port=5000)
