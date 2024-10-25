
"""
Bing Search Topic Explorer
=========================

Purpose:
--------
Explores related searches, suggestions, and topics from a base query
using Bing Web Search API V7. Helps discover potential search directions
for knowledge graph expansion.

Takes a base topic (e.g., "artificial intelligence")
Gets related searches/suggestions
Displays the possibilities for our next searches


This script will:
1. Test all major Bing API endpoints
2. Use proper headers for authentication
3. Show what data each endpoint returns
4. Save detailed results to a file

Each endpoint offers different capabilities:
- /search - General web results
- /suggestions - Query suggestions
- /news - News articles
- /images - Image results
- /videos - Video results
- /entities - Named entities
- /trending - Popular searches

"""

import requests
import json
from datetime import datetime
import time
from typing import Dict, Optional

class BingAPIExplorer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0"
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json",
            "Accept-Language": "en-US"
        }

    def test_endpoint(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Generic endpoint tester with error handling."""
        url = f"{self.base_url}/{endpoint}"
        try:
            print(f"\nTesting endpoint: {endpoint}")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error with endpoint {endpoint}: {str(e)}")
            if hasattr(response, 'text'):
                print(f"Response text: {response.text}")
            return None

    def explore_all_endpoints(self, query: str) -> Dict:
        """Tests all available endpoints with the given query."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "endpoints": {}
        }

        # 1. Web Search (Updated responseFilter)
        print("\nTesting Web Search...")
        results["endpoints"]["search"] = self.test_endpoint("search", {
            "q": query,
            "mkt": "en-US",
            "responseFilter": "Webpages",
            "count": 5
        })
        time.sleep(0.5)  # Rate limiting

        # 2. Suggestions
        print("\nTesting Suggestions...")
        results["endpoints"]["suggestions"] = self.test_endpoint("suggestions", {
            "q": query,
            "mkt": "en-US"
        })
        time.sleep(0.5)

        # 3. News Search
        print("\nTesting News Search...")
        results["endpoints"]["news/search"] = self.test_endpoint("news/search", {
            "q": query,
            "mkt": "en-US",
            "count": 5
        })
        time.sleep(0.5)

        # 4. Image Search
        print("\nTesting Image Search...")
        results["endpoints"]["images/search"] = self.test_endpoint("images/search", {
            "q": query,
            "mkt": "en-US",
            "count": 5
        })
        time.sleep(0.5)

        # 5. Video Search
        print("\nTesting Video Search...")
        results["endpoints"]["videos/search"] = self.test_endpoint("videos/search", {
            "q": query,
            "mkt": "en-US",
            "count": 5
        })
        time.sleep(0.5)

        # 6. Entity Search (Updated endpoint)
        print("\nTesting Entity Search...")
        results["endpoints"]["entities"] = self.test_endpoint("entities", {
            "q": query,
            "mkt": "en-US"
        })
        time.sleep(0.5)

        # 7. Trending Topics (Updated endpoint)
        print("\nTesting Trending Topics...")
        results["endpoints"]["trending"] = self.test_endpoint("trending", {
            "mkt": "en-US"
        })

        return results

    def print_endpoint_summary(self, results: Dict):
        """Prints a summary of endpoint test results with more detail."""
        print("\n" + "="*50)
        print("BING API ENDPOINT SUMMARY")
        print("="*50)
        
        for endpoint, data in results["endpoints"].items():
            if data:
                print(f"\n✅ {endpoint}: Success")
                self._print_endpoint_data(endpoint, data)
            else:
                print(f"\n❌ {endpoint}: Failed")
                
        print("\n" + "="*50)

    def _print_endpoint_data(self, endpoint: str, data: Dict):
        """Prints relevant data based on endpoint type."""
        try:
            if endpoint == "search":
                if "webPages" in data:
                    print("  Sample webpage titles:")
                    for page in data["webPages"]["value"][:2]:
                        print(f"  - {page['name']}")
                        
            elif endpoint == "suggestions":
                if "suggestionGroups" in data:
                    print("  Sample suggestions:")
                    for group in data["suggestionGroups"]:
                        for suggestion in group.get("searchSuggestions", [])[:2]:
                            print(f"  - {suggestion.get('displayText', '')}")
                            
            elif "news" in endpoint:
                if "value" in data:
                    print("  Sample news headlines:")
                    for article in data["value"][:2]:
                        print(f"  - {article.get('name', '')}")
                        
            elif "entities" in endpoint:
                if "value" in data:
                    print("  Sample entities:")
                    for entity in data["value"][:2]:
                        print(f"  - {entity.get('name', '')}")
                        
            elif "trending" in endpoint:
                if "value" in data:
                    print("  Sample trending topics:")
                    for topic in data["value"][:2]:
                        print(f"  - {topic.get('name', '')}")
                        
        except Exception as e:
            print(f"  Error printing data: {str(e)}")

    def save_results(self, results: Dict):
        """Saves API exploration results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bing_api_exploration_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {filename}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")

def main():
    # Your API key
    api_key = "4e2792a37779488794123994c6338469"
    
    # Initialize explorer
    explorer = BingAPIExplorer(api_key)
    
    # Test query
    query = "artificial intelligence"
    print(f"\nTesting all endpoints with query: '{query}'")
    
    # Run exploration
    results = explorer.explore_all_endpoints(query)
    
    # Print summary
    explorer.print_endpoint_summary(results)
    
    # Save results
    explorer.save_results(results)

if __name__ == "__main__":
    main()