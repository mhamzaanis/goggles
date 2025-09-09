# Git Setup Guide

## What to Push to GitHub

### ✅ **Include These Files:**

```
mini-wikipedia-search/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── setup.py                     # Setup script
├── config_template.py           # Configuration template
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
├── python/
│   ├── mass_crawler.py          # Main crawler
│   ├── web_search.py            # Flask web interface
│   ├── advanced_search.py       # ML-powered search
│   ├── launcher.py              # Project launcher
│   └── templates/
│       └── index.html           # Web interface
└── screenshots/                 # Optional: UI screenshots
    └── search-interface.png
```

### ❌ **DON'T Include:**

- `*.log` files (crawler.log, mass_crawler.log)
- `__pycache__/` directories
- `search_model.pkl` (generated file)
- `config.py` (contains passwords)
- `.idea/` (IDE files)
- Database files
- Personal credentials

## Quick Git Commands

### 1. Initialize Repository
```bash
cd "c:\Users\Dell\Desktop\New folder (9)"
git init
git add .
git commit -m "Initial commit: Mini Wikipedia Search Engine"
```

### 2. Create GitHub Repository
1. Go to GitHub.com
2. Click "New Repository"
3. Name: `mini-wikipedia-search`
4. Description: "A lightweight Wikipedia search engine with web interface"
5. Make it Public
6. Don't initialize with README (you already have one)

### 3. Connect to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/mini-wikipedia-search.git
git branch -M main
git push -u origin main
```

### 4. Future Updates
```bash
git add .
git commit -m "Description of changes"
git push
```

## Repository Features to Enable

### GitHub Pages (Optional)
- Go to Settings → Pages
- Source: Deploy from branch
- Branch: main
- This will host your README as a website

### Issues & Projects
- Enable Issues for bug tracking
- Create project boards for feature planning

### GitHub Actions (Advanced)
- Add CI/CD for automated testing
- Auto-deploy documentation

## Example Repository Structure

Your GitHub repo will look like:
```
https://github.com/yourusername/mini-wikipedia-search
├── 📁 python/           # Core application
├── 📄 README.md         # Main documentation
├── 📄 requirements.txt  # Dependencies
├── 📄 LICENSE          # MIT License
├── 📄 .gitignore       # Ignore rules
└── 📄 setup.py         # Setup script
```

## Marketing Your Project

### Good README Features ✅
- Clear project description
- Installation instructions
- Usage examples
- Screenshots
- Feature list
- Contributing guidelines

### GitHub Repository Features ✅
- Topics/tags: `python`, `flask`, `mysql`, `wikipedia`, `search-engine`
- Good repository description
- MIT License for open source
- Professional README

### Portfolio Impact
This project demonstrates:
- **Backend Development**: Python, Flask, MySQL
- **Web Scraping**: Wikipedia API, BeautifulSoup
- **Database Design**: MySQL optimization, indexing
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: TF-IDF, scikit-learn
- **System Design**: Multi-threading, rate limiting
- **DevOps**: Git, documentation, setup scripts
