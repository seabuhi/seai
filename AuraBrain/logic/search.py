import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json

class SearchAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query, max_results=3):
        """Searches Wikipedia instead of DuckDuckGo due to rate limits, returns titles and snippets."""
        results = []
        import requests
        
        # Determine language slightly based on query
        lang = "az" if "nə" in query or "necə" in query or "kodu" in query else "en"
        
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "",
            "format": "json",
            "srlimit": max_results
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            search_hits = data.get("query", {}).get("search", [])
            for hit in search_hits:
                # Strip simple HTML tags from snippet
                import re
                snippet = re.sub(r'<[^>]+>', '', hit['snippet'])
                # Reconstruct a pseudo-href for the scraper just in case
                page_url = f"https://{lang}.wikipedia.org/wiki/{hit['title'].replace(' ', '_')}"
                results.append({
                    "title": hit["title"],
                    "href": page_url,
                    "body": snippet
                })
        except Exception as e:
            print(f"Wikipedia Search error: {e}")
            
        return results

    def search_local_dataset(self, query: str, fp: str = "universal_knowledgebase_v1.txt"):
        """Simple keyword search through the uploaded local dataset."""
        import os
        import re
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_path = os.path.join(base_dir, fp)
        
        if not os.path.exists(dataset_path):
            return None
            
        keywords = [w.lower() for w in query.replace("?", "").replace(",", "").split() if len(w) > 3]
        if not keywords:
            return None
            
        best_match = ""
        max_score = 0
        
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Split roughly by headers or paragraphs
                paragraphs = content.split("\n\n")
                for p in paragraphs:
                    p_lower = p.lower()
                    score = 0
                    for k in keywords:
                        # Exact word matching to prevent 'vaxt' matching 'vaxtı'
                        if re.search(r'\b' + re.escape(k) + r'\b', p_lower):
                            score += 1
                            
                    if score > max_score:
                        max_score = score
                        best_match = p.strip()
                        
            # Require at least half of the keywords to match, or at least 2 if there are many
            min_required = max(1, len(keywords) // 2)
            if len(keywords) > 1 and max_score < 2:
                return None  # Weak match, fallback to web search

            if max_score >= min_required and len(best_match) > 20:
                return best_match
        except Exception as e:
            print(f"Local search error: {e}")
            
        return None

    def scrape_page(self, url):
        """Scrapes text content from a URL."""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            text = soup.get_text(separator=' ')
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:5000] # Limit for now
        except Exception as e:
            print(f"Scrape error: {url} -> {e}")
            return ""

if __name__ == "__main__":
    agent = SearchAgent()
    print("Searching for 'Self-learning AI'...")
    results = agent.search("Self-learning AI", max_results=2)
    for r in results:
        print(f"Title: {r['title']}\nLink: {r['href']}\n")
        # content = agent.scrape_page(r['href'])
        # print(f"Content: {content[:200]}...")
