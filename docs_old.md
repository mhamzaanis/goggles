# Mini Search Engine

A complete mini search engine that crawls Wikipedia articles and provides advanced search functionality with TF-IDF relevance scoring.

## Features

### 🕷️ **Advanced Web Crawler**
- Crawls Wikipedia articles and categories recursively
- Intelligent content filtering (skips low-quality articles)
- HTML content cleaning and text extraction
- Rate limiting and error handling with retry logic
- Progress tracking and logging

### 🔍 **Multiple Search Interfaces**
1. **Command Line Interface** - Interactive terminal-based search
2. **Web Interface** - Modern, responsive web UI
3. **Advanced TF-IDF Search** - Machine learning-based relevance scoring

### 📊 **Search Capabilities**
- **Full-text search** with MySQL FULLTEXT indexes
- **Title-based search** with smart ranking
- **TF-IDF similarity search** using scikit-learn
- **Related articles** discovery
- **Search suggestions** with auto-complete
- **Relevance scoring** and ranking

### 🗄️ **Database Features**
- MySQL storage with optimized indexes
- Clean text extraction from HTML
- Article statistics and metadata
- Duplicate detection and prevention

## File Structure

```
python/
├── launcher.py            # Simple launcher script (START HERE)
├── mass_crawler.py        # Optimized crawler for thousands of articles
├── web_search.py          # Flask web interface
├── advanced_search.py     # TF-IDF based advanced search
├── test_crawler.py        # Test crawler for small samples
├── script.py              # Original crawler with CLI search
├── test_db.py             # Database connection tester
├── templates/
│   └── index.html         # Web interface template
├── mass_crawler.log       # Mass crawler logs (generated)
└── search_model.pkl       # TF-IDF model (generated)
```

## Setup Instructions

### Prerequisites
- Python 3.7+
- MySQL Server running on localhost
- MySQL database named `search_engine_db`
- MySQL user `root` with password `admin` (or modify connection settings)

### Required Python Packages
The setup automatically installs:
- `mysql-connector-python`
- `requests`
- `beautifulsoup4`
- `flask`
- `scikit-learn`
- `numpy`

### Quick Start

**🚀 For tons of articles (Recommended):**
```cmd
python launcher.py
```
Choose option 2 to start mass crawling thousands of articles.

**🌐 Start web interface:**
```cmd
python web_search.py
```

**🧪 Test with sample articles:**
```cmd
python test_crawler.py
```

## Usage Guide

### 1. Web Interface (Recommended)
- Visit `http://localhost:5000`
- Use the search box for queries
- Choose between "Full-text Search" and "Title Search"
- View results with relevance scores
- See database statistics and recent articles

### 2. Command Line Interface
- Run `python script.py`
- After crawling, use interactive commands:
  - `search <query>` - Full-text search
  - `title <query>` - Search by title
  - `stats` - Show database statistics
  - `quit` - Exit

### 3. Advanced TF-IDF Search
- Run `python advanced_search.py`
- Available commands:
  - `search <query>` - Advanced TF-IDF search
  - `related <id>` - Find related articles
  - `suggest <partial>` - Get search suggestions
  - `rebuild` - Rebuild search index
  - `analytics` - Show search analytics

## Database Schema

```sql
CREATE TABLE wiki_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) UNIQUE,
    summary TEXT,
    content LONGTEXT,           -- Raw HTML content
    clean_content LONGTEXT,     -- Cleaned text content
    url VARCHAR(500),
    word_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_word_count (word_count),
    FULLTEXT(title, summary, clean_content)
);
```

## Configuration Options

### Crawler Settings (script.py)
```python
MAX_ARTICLES = 3000          # Maximum articles to crawl
seed_category = "Category:Programming_languages"  # Starting category
```

### Search Settings
```python
# TF-IDF parameters in advanced_search.py
max_features=10000          # Maximum vocabulary size
ngram_range=(1, 2)         # Include unigrams and bigrams
min_df=2                   # Minimum document frequency
max_df=0.8                 # Maximum document frequency
```

## API Endpoints (Web Interface)

- `GET /` - Main search page
- `GET /search?q=<query>&type=<content|title>` - Search API
- `GET /api/stats` - Database statistics
- `GET /api/recent?limit=<n>` - Recent articles

## Search Features Explained

### 1. MySQL Full-text Search
- Uses built-in MySQL FULLTEXT indexes
- Natural language search mode
- Automatic relevance scoring
- Fast performance for basic queries

### 2. TF-IDF Search
- **Term Frequency-Inverse Document Frequency** scoring
- Considers term importance across the corpus
- Better relevance for complex queries
- Supports related article discovery

### 3. Title Search
- Exact and partial title matching
- Smart ranking (exact matches first)
- Useful for finding specific articles

## Performance Tips

1. **For large datasets:**
   - Increase `MAX_ARTICLES` limit
   - Monitor MySQL memory usage
   - Consider index optimization

2. **For faster search:**
   - Rebuild TF-IDF index periodically
   - Adjust `max_features` parameter
   - Use title search for simple queries

3. **For better crawling:**
   - Adjust `time.sleep()` values
   - Monitor API rate limits
   - Use different seed categories

## Troubleshooting

### Common Issues:

1. **Database connection errors:**
   - Check MySQL server is running
   - Verify credentials in connection settings
   - Ensure database `search_engine_db` exists

2. **Memory errors during TF-IDF:**
   - Reduce `max_features` parameter
   - Limit number of articles crawled
   - Increase system RAM

3. **Slow crawling:**
   - Check network connection
   - Verify Wikipedia API is accessible
   - Adjust sleep intervals

4. **No search results:**
   - Ensure articles are crawled first
   - Rebuild search index
   - Check database has content

## Future Enhancements

- [ ] Add search result caching
- [ ] Implement user query logging
- [ ] Add search analytics dashboard
- [ ] Support for multiple languages
- [ ] Advanced filtering options
- [ ] Elasticsearch integration
- [ ] Real-time crawling updates
- [ ] Search result export features

## License

This project is for educational purposes. Please respect Wikipedia's terms of service and API usage guidelines.
