#GREMLIN_USERNAME = f"/dbs/WebScraperDB/colls/Webpages"


from gremlin_python.driver import client, serializer

# Replace these with your Cosmos DB Gremlin endpoint and credentials
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

def test_connection():
    try:
        # Create a Gremlin client
        gremlin_client = client.Client(
            COSMOS_DB_ENDPOINT,
            'g',
            username=f"/dbs/{DATABASE}/colls/{GRAPH}",
            password=COSMOS_DB_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

        # Test the connection by sending a simple Gremlin query
        query = "g.V().limit(1)"
        callback = gremlin_client.submitAsync(query)
        if callback.result():
            print("Connection successful!")
            print("Query result:", callback.result().all().result())
        else:
            print("Connection failed!")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        gremlin_client.close()

if __name__ == "__main__":
    test_connection()
