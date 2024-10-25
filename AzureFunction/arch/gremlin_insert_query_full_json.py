import json
import random
from datetime import datetime
from gremlin_python.driver import client, serializer

# Config variable to choose JSON source
USE_EXTERNAL_JSON = True
JSON_FILE_PATH = "output_json_insert_test_002.json"

# Replace these with your Cosmos DB Gremlin endpoint and credentials
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

def load_json():
    if USE_EXTERNAL_JSON:
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
    else:
        data = {
            "id": f"https_example_com_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "url": "https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/",
            "metadata": {
                "title": "SAP Supercharges Copilot Joule with Collaborative Capabilities to Ignite Enterprise AI Revolution",
                "description": "New collaborative capabilities for Joule and other innovations unveiled at SAP TechEd in 2024 showcase SAPs business AI game changers",
                "keywords": "",
                "canonical_url": "https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/",
                "author": "SAP News",
                "published_time": "2024-10-08T07:02:00+00:00",
                "modified_time": "2024-10-08T12:44:15+00:00",
                "estimated_reading_time": "5 minutes"
            },
            "content": {
                "header": "News Guide AI Innovations to Drive Real Business Outcomes",
                "navigation": "",
                "body": "... (article body content) ...",
                "footer": "... (footer content) ..."
            },
            "images": [
                {
                    "url": "...",
                    "alt": "...",
                    "location": "..."
                }
            ],
            "analysis": {
                "word_count": 1115,
                "readability_score": 0,
                "keywords": ["sap", "ai", "business", "joule"],
                "entities": {}
            },
            "links": [
                {
                    "text": "...",
                    "url": "..."
                }
            ],
            "social_media_metadata": {
                "og": {
                    "locale": "en_US",
                    "type": "article",
                    "title": "...",
                    "description": "...",
                    "url": "...",
                    "site_name": "SAP News Center",
                    "image": "...",
                    "image:width": "...",
                    "image:height": "...",
                    "image:type": "..."
                },
                "twitter": {
                    "card": "summary_large_image",
                    "creator": "@SAPNews",
                    "site": "@SAPNews",
                    "label1": "Written by",
                    "data1": "SAP News",
                    "label2": "Est. reading time",
                    "data2": "5 minutes"
                }
            },
            "structured_data": [
                {
                    "@context": "https://schema.org",
                    "@graph": [
                        {
                            "@type": "Article",
                        },
                        {
                            "@type": "WebPage",
                        }
                    ]
                }
            ]
        }
    return data

def test_gremlin_insert():
    gremlin_client = None
    try:
        # Create a Gremlin client
        gremlin_client = client.Client(
            COSMOS_DB_ENDPOINT,
            'g',
            username=f"/dbs/{DATABASE}/colls/{GRAPH}",
            password=COSMOS_DB_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
        
        # Load JSON data
        data = load_json()
        data["id"] = random.randint(100000, 999999)  # Replace id with a random number

        # Insert a vertex with the provided data
        print("\nInserting test vertex...")
        insert_query = f"""
        g.addV('WebPage')
          .property('id', '{data["id"]}')
          .property('url', '{data["url"]}')
          .property('title', '{data["metadata"]["title"]}')
          .property('description', '{data["metadata"]["description"]}')
          .property('keywords', '{data["metadata"]["keywords"]}')
          .property('canonical_url', '{data["metadata"]["canonical_url"]}')
          .property('author', '{data["metadata"]["author"]}')
          .property('published_time', '{data["metadata"]["published_time"]}')
          .property('modified_time', '{data["metadata"]["modified_time"]}')
          .property('estimated_reading_time', '{data["metadata"]["estimated_reading_time"]}')
          .property('content_header', '{data["content"]["header"]}')
          .property('content_navigation', '{data["content"]["navigation"]}')
          .property('content_body', '{data["content"]["body"]}')
          .property('content_footer', '{data["content"]["footer"]}')
          .property('word_count', {data["analysis"]["word_count"]})
          .property('readability_score', {data["analysis"]["readability_score"]})
          .property('keywords_list', '{json.dumps(data["analysis"]["keywords"])}')
          .property('social_media_metadata', '{json.dumps(data["social_media_metadata"])}')
        """
        insert_callback = gremlin_client.submitAsync(insert_query)
        insert_result = insert_callback.result().all().result()
        print("Insert result:", insert_result)

        # Query to check inserted vertices
        print("\nQuerying for vertices with label 'WebPage'...")
        query = "g.V().hasLabel('WebPage')"
        query_callback = gremlin_client.submitAsync(query)
        query_result = query_callback.result().all().result()
        print("Query result:", query_result)

        # Generate Mermaid diagram
        with open("mermaid_diagram.mmd", "w") as file:
            file.write("graph TD\n")
            for vertex in query_result:
                file.write(f'    {vertex["id"]}["{vertex["properties"]["title"][0]["value"]}"]\n')
            print("Mermaid diagram saved as 'mermaid_diagram.mmd'")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if gremlin_client:
            gremlin_client.close()

if __name__ == "__main__":
    test_gremlin_insert()
