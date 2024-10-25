import azure.functions as func
import logging
from gremlin_python.driver import client, serializer
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="TestFunction")
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Initialize Gremlin client
        gremlin_client = client.Client(
            os.environ['COSMOS_DB_GREMLIN_ENDPOINT'],
            'g',
            username="/dbs/WebScraperDB/colls/WebPages",
            password=os.environ['COSMOS_DB_KEY'],
            message_serializer=serializer.GraphSONSerializersV2d0(),
            transport_factory=lambda: AiohttpTransport(call_from_event_loop=True)
        )

        # Test Gremlin connection
        result = gremlin_client.submitAsync("g.V().count()").result()
        vertex_count = result.one()

        return func.HttpResponse(
            f"Gremlin connection successful. Vertex count: {vertex_count}",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )