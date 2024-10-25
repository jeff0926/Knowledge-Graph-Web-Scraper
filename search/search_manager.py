import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests
from urllib.parse import urlparse

class SearchManager:
    def __init__(self, api_key: str):
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
        self.api_key = api_key
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        # Create output directory if it doesn't exist
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output_json')
        os.makedirs(self.output_dir, exist_ok=True)

    def _clean_filename(self, query: str) -> str:
        """Convert search query to valid filename component."""
        # Replace spaces and special characters
        cleaned = query.lower().replace(' ', '_')
        # Remove any non-alphanumeric chars except underscore
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')
        return cleaned[:50]  # Limit length for filesystem compatibility

    def _generate_filename(self, query: str) -> str:
        """Generate timestamped filename for search results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_query = self._clean_filename(query)
        return f"search_{cleaned_query}_{timestamp}.json"

    def _calculate_priority_score(self, result: Dict) -> float:
        """Calculate priority score for a search result."""
        score = 1.0
        url = urlparse(result['url'])
        
        # Domain authority factors
        if url.netloc.endswith(('.edu', '.gov', '.org')):
            score *= 1.2
        
        # URL structure factors
        if url.query == '':  # Clean URLs without query parameters
            score *= 1.1
        if url.path.count('/') <= 3:  # Prefer shallower paths
            score *= 1.1
            
        # Content relevance factors
        if len(result.get('snippet', '')) > 150:  # Prefer detailed snippets
            score *= 1.1
            
        return min(score, 2.0)  # Cap maximum score

    def search(self, query: str, count: int = 50, market: str = "en-US") -> Optional[str]:
        """
        Execute search and save results to JSON file.
        
        Args:
            query: Search term
            count: Number of results (max 50)
            market: Market code (e.g., "en-US")
            
        Returns:
            Path to output JSON file or None if search failed
        """
        try:
            # Prepare search parameters
            params = {
                "q": query,
                "count": min(count, 20),  # Respect Bing API limit
                "mkt": market,
                "responseFilter": "Webpages"
            }
            
            # Execute search
            response = requests.get(
                self.endpoint,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            # Process results
            search_data = response.json()
            processed_results = []
            
            for result in search_data.get('webPages', {}).get('value', []):
                processed_result = {
                    "url": result['url'],
                    "title": result.get('name', ''),
                    "description": result.get('snippet', ''),
                    "priority_score": self._calculate_priority_score(result),
                    "discovery_date": datetime.now().isoformat(),
                    "domain": urlparse(result['url']).netloc,
                    "status": "pending"
                }
                processed_results.append(processed_result)
            
            # Prepare output data
            output_data = {
                "search_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "total_results": len(processed_results)
                },
                "urls": processed_results
            }
            
            # Save to file
            filename = self._generate_filename(query)
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Search results saved to: {filename}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return None

    def bulk_search(self, queries: List[str], delay: int = 1) -> List[str]:
        """
        Execute multiple searches with delay between requests.
        
        Args:
            queries: List of search terms
            delay: Delay between searches in seconds
            
        Returns:
            List of output file paths
        """
        output_files = []
        
        for query in queries:
            print(f"\nProcessing search: {query}")
            filepath = self.search(query)
            if filepath:
                output_files.append(filepath)
            
            if delay and len(queries) > 1:
                time.sleep(delay)
        
        return output_files

def main():
    """Example usage of SearchManager."""
    # Your API key
    api_key = "4e2792a37779488794123994c6338469"  # Replace with your key
    
    # Initialize search manager
    manager = SearchManager(api_key)
    
    # Example searches
    search_queries = [
        "artificial intelligence research papers",
        "machine learning algorithms"
    ]
    
    # Execute searches
    output_files = manager.bulk_search(search_queries)
    
    # Report results
    print("\nSearch Summary:")
    for filepath in output_files:
        print(f"✅ Generated: {os.path.basename(filepath)}")

if __name__ == "__main__":
    main()