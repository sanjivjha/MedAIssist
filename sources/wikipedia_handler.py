# sources/wikipedia_handler.py
from .base_handler import BaseSourceHandler
import wikipedia

class WikipediaHandler(BaseSourceHandler):
    def fetch_data(self, query: str) -> list:
        try:
            page = wikipedia.page(query)
            return [f"Title: {page.title}\nContent: {page.summary}"]
        except wikipedia.exceptions.DisambiguationError as e:
            return [f"Multiple pages found for '{query}'. Possible matches: {', '.join(e.options[:5])}"]
        except wikipedia.exceptions.PageError:
            return [f"No Wikipedia page found for '{query}'"]