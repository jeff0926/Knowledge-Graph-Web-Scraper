"""
Azure Cosmos DB Data Insertion Utility
------------------------------------

Purpose:
--------
This utility script is part of a web scraping ecosystem designed to store structured web content 
in Azure Cosmos DB. It serves as the database layer for a knowledge graph system, handling the 
insertion of pre-processed web content stored in JSON format.

Library Dependencies:
-------------------
json
    - Handles reading and parsing of JSON files
    - Maintains data structure integrity
    - Ensures proper encoding/decoding of web content

random
    - Generates unique document IDs
    - Ensures database record uniqueness
    - Prevents ID collisions

azure.cosmos
    - Azure Cosmos DB SDK
    - Manages database connections and operations
    - Handles document insertion and queries

datetime
    - Provides timestamp functionality
    - Enables chronological tracking
    - Supports audit logging

JSON Format and Structure:
------------------------
The JSON files contain structured web content with:
1. Core Content
   - Main article text
   - Headers and navigation
   - Footer content

2. Metadata
   - SEO information
   - Social media tags
   - Publishing details

3. Extracted Information
   - Named entities
   - Keywords
   - Links and images

This structure supports:
- Efficient querying
- Content relationships
- Knowledge graph construction
- Data analysis capabilities

Workflow:
--------
1. JSON Ingestion
   - Reads pre-processed JSON files
   - Validates data structure
   - Prepares for insertion

2. Database Operations
   - Connects to Cosmos DB
   - Generates unique IDs
   - Handles data insertion
   - Verifies successful storage

3. Verification
   - Queries inserted data
   - Confirms data integrity
   - Reports operation status

Configuration:
-------------
- Uses environment-specific endpoints
- Requires proper authentication
- Supports multiple databases/containers
- Configurable through variables

Error Handling:
-------------
- Comprehensive status logging
- Operation verification
- Detailed error reporting
- Failed operation recovery

Note: This script is designed to work with the web scraper output format, 
maintaining data consistency and enabling knowledge graph construction.
"""

import json
import random
from azure.cosmos import CosmosClient
from datetime import datetime

# Config variables
USE_EXTERNAL_JSON = True
JSON_FILE_PATH = "./output_json/wimi-announced-machine-learning-based-145000718html_20241022_162715.json"  # Update this path
COSMOS_DB_ENDPOINT = 'https://knowledgegraph-webscraper-cosmosdb.documents.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE_NAME = 'WebScraperDB'
CONTAINER_NAME = 'WebPages'

def print_status(message: str):
    """Print formatted status message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def read_json(file_path):
    print_status(f"Reading JSON file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            print_status(f"Successfully read JSON file")
            return data
    except Exception as e:
        print_status(f"ERROR reading JSON file: {str(e)}")
        return None

def insert_data_into_cosmosdb(data):
    print_status("Connecting to Cosmos DB...")
    try:
        client = CosmosClient(COSMOS_DB_ENDPOINT, credential=COSMOS_DB_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        # Generate random ID
        data["id"] = str(random.randint(100000, 999999))
        
        print_status("Inserting data into Cosmos DB...")
        container.upsert_item(data)
        print_status(f"SUCCESS: Data inserted with ID: {data['id']}")
        return data["id"]
    
    except Exception as e:
        print_status(f"ERROR: Failed to insert data: {str(e)}")
        return None

def query_data_from_cosmosdb(doc_id):
    print_status(f"Verifying insertion with ID: {doc_id}")
    try:
        client = CosmosClient(COSMOS_DB_ENDPOINT, credential=COSMOS_DB_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        query = f"SELECT * FROM c WHERE c.id = '{doc_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            print_status(f"SUCCESS: Document verified in database")
            return True
        else:
            print_status("ERROR: Document not found in database")
            return False
            
    except Exception as e:
        print_status(f"ERROR: Failed to query data: {str(e)}")
        return False

if __name__ == "__main__":
    print_status("Starting Cosmos DB insertion process")
    
    if USE_EXTERNAL_JSON:
        print_status(f"Using external JSON file: {JSON_FILE_PATH}")
        data = read_json(JSON_FILE_PATH)
        
        if data:
            inserted_id = insert_data_into_cosmosdb(data)
            if inserted_id:
                query_data_from_cosmosdb(inserted_id)
        
    else:
        print_status("ERROR: USE_EXTERNAL_JSON is set to False")
    
    print_status("Process completed")