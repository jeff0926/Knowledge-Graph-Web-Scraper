#GREMLIN_USERNAME = f"/dbs/WebScraperDB/colls/Webpages"
#username=f"/dbs/WebScraperDB/colls/Webpages",
import json
from datetime import datetime
from gremlin_python.driver import client, serializer

# Replace these with your Cosmos DB Gremlin endpoint and credentials
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

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
        
        # Insert a vertex with a unique ID
        print("\nInserting test vertex...")
        unique_id = f"https_example_com_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        insert_query = f"""
        g.addV('WebPage')
          .property('id', '{unique_id}')
          .property('url', 'https://example.com')
          .property('title', 'Example Page')
          .property('description', 'This is an example page')
          .property('content', 'This is the main content of the page.')
          .property('word_count', 10)
          .property('readability_score', 70.5)
          .property('keywords', '["example", "page", "content"]')
          .property('social_media_metadata', '{{"og":{{"title":"Example Page"}},"twitter":{{"card":"summary"}}}}')
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
