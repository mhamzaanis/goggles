import mysql.connector
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from typing import List, Dict, Any, Tuple
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSearchEngine:
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="search_engine_db"
        )
        self.cursor = self.db.cursor()
        self.vectorizer = None
        self.tfidf_matrix = None
        self.article_ids = []
        self.model_file = 'search_model.pkl'
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for better search results."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def build_search_index(self):
        """Build TF-IDF search index from database content."""
        logger.info("Building search index...")
        
        # Check if table exists first
        try:
            self.cursor.execute("SHOW TABLES LIKE 'wiki_articles'")
            if not self.cursor.fetchone():
                logger.error("Table 'wiki_articles' not found. Please run the crawler first.")
                return False
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False
        
        # Fetch all articles
        self.cursor.execute("""
            SELECT id, title, summary, clean_content 
            FROM wiki_articles 
            WHERE clean_content IS NOT NULL 
            AND LENGTH(clean_content) > 100
            ORDER BY id
        """)
        
        articles = self.cursor.fetchall()
        
        if not articles:
            logger.warning("No articles found with clean content. Please run the crawler first to populate the database.")
            return False
            
        logger.info(f"Processing {len(articles)} articles for search index")
        
        # Prepare documents and IDs
        documents = []
        self.article_ids = []
        
        for article_id, title, summary, content in articles:
            # Combine title, summary, and content with weights
            # Title gets more weight by repeating it
            doc_text = f"{title} {title} {title} {summary} {content}"
            doc_text = self.preprocess_text(doc_text)
            
            documents.append(doc_text)
            self.article_ids.append(article_id)
        
        if not documents:
            logger.warning("No documents found for indexing")
            return False
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=10000,  # Limit vocabulary size
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.8  # Ignore terms that appear in more than 80% of documents
        )
        
        # Fit and transform documents
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        
        # Save the model
        self.save_model()
        
        logger.info(f"Search index built with {len(documents)} documents and {len(self.vectorizer.vocabulary_)} features")
        return True
    
    def save_model(self):
        """Save the trained model to disk."""
        model_data = {
            'vectorizer': self.vectorizer,
            'tfidf_matrix': self.tfidf_matrix,
            'article_ids': self.article_ids
        }
        
        with open(self.model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {self.model_file}")
    
    def load_model(self):
        """Load the trained model from disk."""
        if not os.path.exists(self.model_file):
            logger.warning(f"Model file {self.model_file} not found. Building new index...")
            return self.build_search_index()
        
        try:
            with open(self.model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data['vectorizer']
            self.tfidf_matrix = model_data['tfidf_matrix']
            self.article_ids = model_data['article_ids']
            
            logger.info(f"Model loaded from {self.model_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return self.build_search_index()
    
    def advanced_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Perform advanced TF-IDF based search."""
        if not self.vectorizer or self.tfidf_matrix is None:
            logger.error("Search index not initialized")
            return []
        
        # Preprocess query
        processed_query = self.preprocess_text(query)
        
        # Transform query using the fitted vectorizer
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top results
        top_indices = similarities.argsort()[-limit:][::-1]
        
        # Filter out results with very low similarity
        results = []
        for idx in top_indices:
            similarity_score = similarities[idx]
            if similarity_score > 0.01:  # Minimum threshold
                article_id = self.article_ids[idx]
                
                # Fetch article details
                self.cursor.execute("""
                    SELECT title, summary, url, word_count
                    FROM wiki_articles 
                    WHERE id = %s
                """, (article_id,))
                
                article_data = self.cursor.fetchone()
                if article_data:
                    results.append({
                        'id': article_id,
                        'title': article_data[0],
                        'summary': article_data[1],
                        'url': article_data[2],
                        'word_count': article_data[3],
                        'relevance': float(similarity_score)
                    })
        
        return results
    
    def get_related_articles(self, article_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Find articles similar to a given article."""
        if not self.vectorizer or self.tfidf_matrix is None:
            return []
        
        try:
            # Find the index of the given article
            target_idx = self.article_ids.index(article_id)
            
            # Get the TF-IDF vector for this article
            target_vector = self.tfidf_matrix[target_idx]
            
            # Calculate similarities with all other articles
            similarities = cosine_similarity(target_vector, self.tfidf_matrix).flatten()
            
            # Get top similar articles (excluding the target article itself)
            top_indices = similarities.argsort()[-limit-1:][::-1]
            
            results = []
            for idx in top_indices:
                if idx != target_idx and similarities[idx] > 0.1:
                    related_id = self.article_ids[idx]
                    
                    self.cursor.execute("""
                        SELECT title, summary, url, word_count
                        FROM wiki_articles 
                        WHERE id = %s
                    """, (related_id,))
                    
                    article_data = self.cursor.fetchone()
                    if article_data:
                        results.append({
                            'id': related_id,
                            'title': article_data[0],
                            'summary': article_data[1],
                            'url': article_data[2],
                            'word_count': article_data[3],
                            'similarity': float(similarities[idx])
                        })
            
            return results[:limit]
        
        except ValueError:
            logger.warning(f"Article ID {article_id} not found in search index")
            return []
    
    def search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        if len(partial_query) < 2:
            return []
        
        try:
            # Search for titles that start with or contain the partial query
            sql = """
            SELECT DISTINCT title
            FROM wiki_articles 
            WHERE title LIKE %s OR title LIKE %s
            ORDER BY 
                CASE 
                    WHEN title LIKE %s THEN 1
                    ELSE 2
                END,
                LENGTH(title)
            LIMIT %s
            """
            
            starts_pattern = f"{partial_query}%"
            contains_pattern = f"%{partial_query}%"
            
            self.cursor.execute(sql, (starts_pattern, contains_pattern, starts_pattern, limit))
            results = self.cursor.fetchall()
            
            return [result[0] for result in results]
        
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics about the search index."""
        if not self.vectorizer or self.tfidf_matrix is None:
            return {}
        
        return {
            'total_documents': self.tfidf_matrix.shape[0],
            'vocabulary_size': len(self.vectorizer.vocabulary_),
            'feature_names_sample': list(self.vectorizer.get_feature_names_out()[:20]),
            'matrix_density': self.tfidf_matrix.nnz / (self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1])
        }

def main():
    """Command line interface for advanced search."""
    print("Initializing Advanced Search Engine...")
    
    try:
        engine = AdvancedSearchEngine()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        print("\nPlease ensure:")
        print("1. MySQL server is running")
        print("2. Database 'search_engine_db' exists")
        print("3. User credentials are correct")
        print("4. Run the crawler first: python script.py")
        return
    
    if not engine.load_model():
        print("Failed to initialize search engine")
        print("\nTo get started:")
        print("1. First run the crawler to collect articles: python script.py")
        print("2. Then rebuild the search index with the 'rebuild' command")
        return
    
    analytics = engine.get_search_analytics()
    print(f"Search engine ready!")
    print(f"- Indexed documents: {analytics.get('total_documents', 0)}")
    print(f"- Vocabulary size: {analytics.get('vocabulary_size', 0)}")
    print(f"- Matrix density: {analytics.get('matrix_density', 0):.4f}")
    
    print("\nCommands:")
    print("  search <query>     - Advanced TF-IDF search")
    print("  related <id>       - Find related articles")
    print("  suggest <partial>  - Get search suggestions")
    print("  rebuild            - Rebuild search index")
    print("  analytics          - Show search analytics")
    print("  quit               - Exit")
    print("-" * 60)
    
    while True:
        try:
            command = input("\nEnter command: ").strip()
            
            if command.lower() == 'quit':
                break
            elif command.lower() == 'rebuild':
                print("Rebuilding search index...")
                if engine.build_search_index():
                    print("Search index rebuilt successfully!")
                else:
                    print("Failed to rebuild search index")
            elif command.lower() == 'analytics':
                analytics = engine.get_search_analytics()
                print("\nSearch Analytics:")
                for key, value in analytics.items():
                    print(f"  {key}: {value}")
            elif command.startswith('search '):
                query = command[7:].strip()
                if query:
                    results = engine.advanced_search(query)
                    print(f"\nFound {len(results)} results for '{query}':")
                    print("-" * 50)
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result['title']}")
                        print(f"   Relevance: {result['relevance']:.4f} | Words: {result['word_count']}")
                        print(f"   Summary: {result['summary'][:150]}...")
                        print(f"   URL: {result['url']}")
                        print()
            elif command.startswith('related '):
                try:
                    article_id = int(command[8:].strip())
                    results = engine.get_related_articles(article_id)
                    print(f"\nFound {len(results)} related articles:")
                    print("-" * 50)
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result['title']}")
                        print(f"   Similarity: {result['similarity']:.4f} | Words: {result['word_count']}")
                        print(f"   URL: {result['url']}")
                        print()
                except ValueError:
                    print("Please provide a valid article ID")
            elif command.startswith('suggest '):
                partial = command[8:].strip()
                if partial:
                    suggestions = engine.search_suggestions(partial)
                    print(f"\nSuggestions for '{partial}':")
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
