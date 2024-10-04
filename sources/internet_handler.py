from .base_handler import BaseSourceHandler
from duckduckgo_search import DDGS

class InternetHandler(BaseSourceHandler):
    def fetch_data(self, query: str) -> list:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
            return [f"Title: {result['title']}\nSnippet: {result['body']}\nURL: {result['href']}" for result in results]
        except Exception as e:
            print(f"Error in Internet search: {str(e)}")
            return []