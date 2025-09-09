# Mini Wikipedia Search Engine

A lightweight search engine that crawls Wikipedia articles and provides a web interface for searching through the collected content.

## Features

- **Wikipedia Crawler**: Efficiently crawls and stores Wikipedia articles
- **Web Interface**: Clean, responsive search interface
- **Full-text Search**: MySQL-powered full-text search capabilities
- **Advanced Search**: ML-powered search with TF-IDF and cosine similarity
- **Multi-threaded**: Concurrent crawling for better performance

## Screenshots

![Search Interface](screenshots/search-interface.png)
*Main search interface with clean, responsive design*

## Installation

### Prerequisites
- Python 3.8+
- MySQL Server
- Git

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/mini-wikipedia-search.git
cd mini-wikipedia-search
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup MySQL Database**
```sql
CREATE DATABASE search_engine_db;
CREATE USER 'search_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON search_engine_db.* TO 'search_user'@'localhost';
FLUSH PRIVILEGES;
```

4. **Configure Database Connection**
Edit the database configuration in the Python files:
```python
# Update these values in mass_crawler.py and web_search.py
host="localhost"
user="your_username"  # Change from "root"
password="your_password"  # Change from "admin"
database="search_engine_db"
```

## Usage

### 1. Start the Crawler
```bash
python mass_crawler.py
```
The crawler will:
- Fetch articles from Wikipedia
- Store them in MySQL database
- Target: 10,000 articles
- Uses 5 concurrent threads

### 2. Launch Web Interface
```bash
python web_search.py
```
Visit `http://localhost:5000` to access the search interface.

### 3. Use Advanced Search
```bash
python advanced_search.py
```
For ML-powered search with TF-IDF and similarity scoring.

### 4. Quick Launch (All-in-One)
```bash
python launcher.py
```

## Project Structure

```
mini-wikipedia-search/
├── mass_crawler.py      # Main Wikipedia crawler
├── web_search.py        # Flask web interface
├── advanced_search.py   # ML-powered search
├── launcher.py          # Project launcher
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── templates/
│   └── index.html      # Web interface template
├── screenshots/
│   └── search-interface.png
└── docs/
    └── setup-guide.md
```

## Configuration

### Database Settings
- **Host**: localhost
- **Database**: search_engine_db
- **Tables**: wiki_articles (auto-created)

### Crawler Settings
```python
MAX_ARTICLES = 10000    # Target number of articles
MAX_WORKERS = 5         # Concurrent threads
BATCH_SIZE = 100        # Database batch size
RATE_LIMIT = 0.2        # Seconds between requests
```

### Web Server Settings
```python
HOST = '0.0.0.0'        # Listen on all interfaces
PORT = 5000             # Default Flask port
DEBUG = True            # Development mode
```

## API Endpoints

- `GET /` - Main search interface
- `GET /search?q=query&type=content` - Search articles
- `GET /api/stats` - Database statistics
- `GET /api/recent` - Recent articles

## Features

### 🔍 **Search Capabilities**
- Full-text search across title, summary, and content
- Title-only search for specific articles
- Relevance scoring and ranking
- Fast MySQL FULLTEXT indexing

### 🚀 **Performance**
- Multi-threaded crawling (5 concurrent workers)
- Batch database operations (100 articles per batch)
- Rate limiting to respect Wikipedia's servers
- Optimized MySQL indexes

### 🛡️ **Reliability**
- Graceful shutdown on interruption
- Database connection cleanup
- Error handling and logging
- Duplicate article prevention

### 🎨 **User Interface**
- Clean, modern design
- Responsive layout
- Real-time search results
- Search statistics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Wikipedia API for providing access to articles
- Flask for the web framework
- MySQL for database storage
- BeautifulSoup for HTML parsing

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```
mysql.connector.errors.ProgrammingError: 1045 (28000): Access denied
```
- Check your MySQL credentials
- Ensure MySQL server is running
- Verify user permissions

**2. Port Already in Use**
```
OSError: [Errno 48] Address already in use
```
- Stop existing Flask processes
- Use a different port: `app.run(port=5001)`

**3. Import Errors**
```
ModuleNotFoundError: No module named 'flask'
```
- Install requirements: `pip install -r requirements.txt`
- Check Python environment

### Performance Tips

- **Increase worker threads** for faster crawling (but respect Wikipedia's rate limits)
- **Optimize MySQL** with proper indexing
- **Use SSD storage** for better database performance
- **Monitor memory usage** during large crawls

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/mini-wikipedia-search/issues) page
2. Search existing issues before creating a new one
3. Provide detailed error messages and system information

---

**Happy Searching!** 🔍✨
