from .base_handler import BaseSourceHandler
from pymed import PubMed
from config import Config

class PubmedHandler(BaseSourceHandler):
    def __init__(self):
        self.pubmed = PubMed(tool="MyTool", email="my@email.address")

    def fetch_data(self, query: str) -> list:
        try:
            if not query.strip():
                return []

            enhanced_query = f"{query} AND (english[Language])"
            results = self.pubmed.query(enhanced_query, max_results=Config.MAX_RESULTS)
            documents = []
            
            for article in results:
                title = getattr(article, 'title', 'No title available')
                abstract = getattr(article, 'abstract', 'No abstract available')
                if title or abstract:
                    documents.append(f"Title: {title}\nAbstract: {abstract}")
            
            print(f"PubMed query '{enhanced_query}' returned {len(documents)} results")
            return documents
        except Exception as e:
            print(f"Error in PubMed query: {str(e)}")
            return []