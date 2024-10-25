import json
import random
from azure.cosmos import CosmosClient

# Config variables
USE_EXTERNAL_JSON = True
JSON_FILE_PATH = "https_apnews_com_article_liam-payne-dies-one-direction-6b7893a56e0d8701096775f611399dd8.json"  # Update this path
COSMOS_DB_ENDPOINT = 'https://knowledgegraph-webscraper-cosmosdb.documents.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE_NAME = 'WebScraperDB'
CONTAINER_NAME = 'WebPages'


def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

def insert_data_into_cosmosdb(data):
    try:
        client = CosmosClient(COSMOS_DB_ENDPOINT, credential=COSMOS_DB_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        data["id"] = str(random.randint(100000, 999999))  # Add a unique id to the document
        container.upsert_item(data)
        print(f"Data inserted successfully into Cosmos DB with id: {data['id']}")
        return data["id"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def query_data_from_cosmosdb(doc_id):
    try:
        client = CosmosClient(COSMOS_DB_ENDPOINT, credential=COSMOS_DB_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        query = f"SELECT * FROM c WHERE c.id = '{doc_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        if items:
            print(f"Retrieved document: {json.dumps(items[0], indent=4)}")
            return items[0]
        else:
            print("No document found with the provided id.")
            return None
    except Exception as e:
        print(f"An error occurred while querying data: {e}")
        return None

if USE_EXTERNAL_JSON:
    data = read_json(JSON_FILE_PATH)
    inserted_id = insert_data_into_cosmosdb(data)
    if inserted_id:
        query_data_from_cosmosdb(inserted_id)
else:
    print("Set USE_EXTERNAL_JSON to True and provide a valid JSON file path.")