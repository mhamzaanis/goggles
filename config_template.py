# Database Configuration Template
# Copy this file to config.py and update with your actual credentials

# MySQL Database Settings
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',      # Change this
    'password': 'your_password',  # Change this  
    'database': 'search_engine_db'
}

# Flask Settings
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Crawler Settings
CRAWLER_CONFIG = {
    'max_articles': 10000,
    'max_workers': 5,
    'batch_size': 100,
    'rate_limit': 0.2
}

# Wikipedia API Settings
HEADERS = {
    'User-Agent': 'Mini Search Engine Bot/1.0 (Educational Project; Contact: your-email@example.com)'
}
