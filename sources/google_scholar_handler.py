from .base_handler import BaseSourceHandler
from scholarly import scholarly
from config import Config

class GoogleScholarHandler(BaseSourceHandler):
    def fetch_data(self, query: str) -> list:
        try:
            # Ensure the query is not empty
            if not query.strip():
                return []

            search_query = scholarly.search_pubs(query)
            documents = []
            for i in range(Config.MAX_RESULTS):
                try:
                    article = next(search_query)
                    if 'title' in article['bib'] and 'abstract' in article['bib']:
                        documents.append(f"Title: {article['bib']['title']}\nAbstract: {article['bib']['abstract']}")
                except StopIteration:
                    break
                except Exception as e:
                    print(f"Error processing Google Scholar result: {str(e)}")
            
            print(f"Google Scholar query '{query}' returned {len(documents)} results")
            return documents
        except Exception as e:
            print(f"Error in Google Scholar query: {str(e)}")
            return []