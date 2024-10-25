from gremlin_python.driver import client, serializer
import logging
import json
import uuid


print("\n****************************gremlin_insert_full_json.py ****************************")

# Cosmos DB configuration
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

def create_gremlin_client():
    return client.Client(
        COSMOS_DB_ENDPOINT,
        'g',
        username=f"/dbs/{DATABASE}/colls/{GRAPH}",
        password=COSMOS_DB_KEY,
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

def insert_webpage_data(data):
    gremlin_client = None
    try:
        gremlin_client = create_gremlin_client()
        
        logging.info(f"Received data type: {type(data)}")
        logging.info(f"Received data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")
        
        # Flatten and prepare metadata fields properly
        #metadata_str = json.dumps(data.get('metadata', {})).replace("'", "\\'")
        #social_media_metadata_str = json.dumps(data.get('social_media_metadata', {})).replace("'", "\\'")
        # Replace the f-string with format method

        # Generate a unique ID instead of using the URL
        generated_id = str(uuid.uuid4())

 # Replace the f-string with format method
        insert_query = """
            g.addV('WebPage')
                .property('id', '{id}')
                .property('url', '{url}')
                .property('title', '{title}')
                .property('description', '{description}')
                .property('keywords', '{keywords}')
                .property('canonical_url', '{canonical_url}')
                .property('author', '{author}')
                .property('published_time', '{published_time}')
                .property('modified_time', '{modified_time}')
                .property('content_header', '{content_header}')
                .property('content_body', '{content_body}')
                .property('social_media_metadata', '{social_media_metadata}')
        """.format(
            id=generated_id,
            url=data["url"],
            title=data.get("metadata", {}).get("title", "").replace("'", "\\'"),
            description=data.get("metadata", {}).get("description", "").replace("'", "\\'"),
            keywords=data.get("metadata", {}).get("keywords", "").replace("'", "\\'"),
            canonical_url=data.get("metadata", {}).get("canonical_url", "").replace("'", "\\'"),
            author=data.get("metadata", {}).get("author", "").replace("'", "\\'"),
            published_time=data.get("metadata", {}).get("published_time", "").replace("'", "\\'"),
            modified_time=data.get("metadata", {}).get("modified_time", "").replace("'", "\\'"),
            content_header=data.get("content", {}).get("header", "").replace("'", "\\'"),
            content_body=data.get("content", {}).get("body", "").replace("'", "\\'"),
            social_media_metadata=json.dumps(data.get("social_media_metadata", {})).replace("'", "\\'")
        )

        result = gremlin_client.submitAsync(insert_query).result()
        return {"status": "success", "result": result}

    except Exception as e:
        logging.error(f"Error inserting data: {str(e)}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        return {"status": "error", "error": str(e)}
    finally:
        if gremlin_client:
            gremlin_client.close()
# This part is for testing the script independently
if __name__ == "__main__":
    test_data = {
        "id": "test_id",
        "url": "https://jeffrey.com",
        "description": "Test description",
        "content": {"body": "Test content"},
        "metadata": {"title": "Test Title"},
        "social_media_metadata": {},
        "word_count": 100,
        "readability_score": 50.0,
        "keywords": ["test", "example"],
        "entities": {},
        "structured_data": [],
        "images": [],
        "processed_json_ld": []
    }
    result = insert_webpage_data(test_data)
    