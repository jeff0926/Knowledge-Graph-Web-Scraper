import os
import sys
import requests
from datetime import datetime
import json

class BingHealthCheck:
    def __init__(self):
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
        #self.api_key = os.getenv('BING_API_KEY')
        self.api_key = '4e2792a37779488794123994c6338469'
        self.test_query = "test query"
        self.results = {
            "environment": False,
            "api_connection": False,
            "search_capability": False
        }
        
    def check_environment(self):
        """Verify environment setup and API key availability."""
        print("\n1. Checking API Key Setup...")
        
        if not self.api_key:
            print("❌ BING_API_KEY not found")
            return False
            
        print("✅ BING_API_KEY found in environment variables")
        self.results["environment"] = True
        return True

    def test_api_connection(self):
        """Test basic connectivity to Bing API endpoint."""
        print("\n2. Testing API Connection...")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        try:
            response = requests.get(
                self.endpoint,
                headers=headers,
                params={"q": self.test_query, "count": 1}
            )
            
            if response.status_code == 200:
                print("✅ Successfully connected to Bing API")
                self.results["api_connection"] = True
                return True
            else:
                print(f"❌ API request failed with status code: {response.status_code}")
                print(f"  → Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {str(e)}")
            return False

    def test_search_capability(self):
        """Test actual search functionality and response parsing."""
        print("\n3. Testing Search Capability...")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        try:
            response = requests.get(
                self.endpoint,
                headers=headers,
                params={
                    "q": "artificial intelligence",
                    "count": 2,
                    "mkt": "en-US"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "webPages" in data and "value" in data["webPages"]:
                    results = data["webPages"]["value"]
                    if len(results) > 0:
                        print("✅ Search functionality working correctly")
                        print("\nSample Search Result:")
                        print(f"  Title: {results[0]['name']}")
                        print(f"  URL: {results[0]['url']}")
                        self.results["search_capability"] = True
                        return True
                
                print("❌ Unexpected response format")
                print(f"  → Response: {json.dumps(data, indent=2)}")
                return False
                
        except Exception as e:
            print(f"❌ Search test failed: {str(e)}")
            return False

    def run_health_check(self):
        """Run all health checks and provide summary."""
        print("=== Bing Search API Health Check ===")
        print(f"Timestamp: {datetime.now()}")
        print(f"Endpoint: {self.endpoint}")
        
        # Run checks
        env_check = self.check_environment()
        if env_check:
            api_check = self.test_api_connection()
            if api_check:
                self.test_search_capability()
        
        # Print summary
        print("\n=== Health Check Summary ===")
        for check, status in self.results.items():
            status_symbol = "✅" if status else "❌"
            print(f"{status_symbol} {check.replace('_', ' ').title()}")
        
        # Return overall status
        return all(self.results.values())

if __name__ == "__main__":
    checker = BingHealthCheck()
    success = checker.run_health_check()
    sys.exit(0 if success else 1)