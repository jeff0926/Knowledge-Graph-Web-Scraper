import json
import random
import os
from datetime import datetime
from gremlin_python.driver import client, serializer

# Config variable to choose JSON source
USE_EXTERNAL_JSON = True
JSON_FILE_PATH = "https_apnews_com_article_liam-payne-dies-one-direction-6b7893a56e0d8701096775f611399dd8.json"
#webpage_data_467792.json

# Replace these with your Cosmos DB Gremlin endpoint and credentials
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

OUTPUT_DIR = "output_json"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_json():
    if USE_EXTERNAL_JSON:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
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

def save_json_to_file(data, filename):
    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Saved JSON data to {output_path}")

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

        # Save the JSON data to a file in the output_json directory
        save_json_to_file(data, f'webpage_data_{data["id"]}.json')

        # Assign default values for missing fields
        metadata = data.get("metadata", {})
        title = metadata.get("title", "Unknown Title")
        description = metadata.get("description", "")
        keywords = metadata.get("keywords", "")
        canonical_url = metadata.get("canonical_url", "")
        author = metadata.get("author", "Unknown Author")
        published_time = metadata.get("published_time", "")
        modified_time = metadata.get("modified_time", "")
        estimated_reading_time = metadata.get("estimated_reading_time", "")

        # Insert a vertex with the provided data
        print("\nInserting test vertex...")
        insert_query = f"""
        g.addV('WebPage')
          .property('id', '{data["id"]}')
          .property('url', '{data["url"]}')
          .property('title', '{title}')
          .property('description', '{description}')
          .property('keywords', '{keywords}')
          .property('canonical_url', '{canonical_url}')
          .property('author', '{author}')
          .property('published_time', '{published_time}')
          .property('modified_time', '{modified_time}')
          .property('estimated_reading_time', '{estimated_reading_time}')
          .property('content_header', '{data.get("content", {}).get("header", "")}')
          .property('content_body', '{data.get("content", {}).get("body", "")}')
          .property('word_count', {data.get("analysis", {}).get("word_count", 0)})
          .property('readability_score', {data.get("analysis", {}).get("readability_score", 0)})
          .property('keywords_list', '{json.dumps(data.get("analysis", {}).get("keywords", []))}')
          .property('social_media_metadata', '{json.dumps(data.get("social_media_metadata", {}))}')
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

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if gremlin_client:
            gremlin_client.close()

if __name__ == "__main__":
    test_gremlin_insert()
