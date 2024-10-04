import sys
from sources.pubmed_handler import PubmedHandler
from sources.google_scholar_handler import GoogleScholarHandler
from sources.wikipedia_handler import WikipediaHandler
from sources.internet_handler import InternetHandler

def test_handlers(query):
    handlers = {
        "PubMed": PubmedHandler(),
        "Google Scholar": GoogleScholarHandler(),
        "Wikipedia": WikipediaHandler(),
        "Internet": InternetHandler()
    }

    for name, handler in handlers.items():
        print(f"\nTesting {name} Handler:")
        try:
            results = handler.fetch_data(query)
            print(f"{name} returned {len(results)} results")
            if results:
                print("First result snippet:")
                print(results[0][:200] + "..." if len(results[0]) > 200 else results[0])
            else:
                print("No results found.")
        except Exception as e:
            print(f"Error testing {name} handler: {str(e)}")

if __name__ == "__main__":
    default_query = "COVID-19 treatment"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = default_query
        print(f"No query provided. Using default query: '{default_query}'")
    
    print(f"Testing handlers with query: '{query}'\n")
    test_handlers(query)