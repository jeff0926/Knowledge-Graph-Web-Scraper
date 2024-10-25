import logging
import azure.functions as func
print("Azure Functions import successful")
import requests
print("Requests import successful")
from bs4 import BeautifulSoup
print("BeautifulSoup import successful")
import json
import os
from gremlin_python.driver import client, serializer
print("Basic gremlin import successful")
from azure.ai.textanalytics import TextAnalyticsClient
print("Text Analytics import successful")
from azure.core.credentials import AzureKeyCredential
from gremlin_python.driver.transport import AsyncioTransport
print("AsyncioTransport import successful")
import sys

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Set up the Gremlin client
gremlin_client = client.Client(
    os.environ['COSMOS_DB_GREMLIN_ENDPOINT'],
    'g',
    username="/dbs/WebScraperDB/colls/WebPages",
    password=os.environ['COSMOS_DB_KEY'],
    message_serializer=serializer.GraphSONSerializersV2d0(),
    transport_factory=lambda: AsyncioTransport(call_from_event_loop=True)
)

# Set up the Text Analytics client
text_analytics_client = TextAnalyticsClient(
    endpoint=os.environ['TEXT_ANALYTICS_ENDPOINT'],
    credential=AzureKeyCredential(os.environ['TEXT_ANALYTICS_KEY'])
)

@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Get the JSON body from the request
        req_body = req.get_json()
        logging.info(f"Received request body: {req_body}")
        url = req_body.get('url')

        if not url:
            raise ValueError("URL is missing in the request.")

        # Fetch the webpage content
        response = requests.get(url)
        html_content = response.text

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract components
        header = soup.find('header')
        navigation = soup.find('nav')
        content = soup.find('main') or soup.find('body')
        footer = soup.find('footer')
        metadata = {
            'title': soup.title.string if soup.title else '',
            'description': '',
            'keywords': ''
        }

        # Extract meta description and keywords
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                metadata['description'] = meta.get('content', '')
            if meta.get('name') == 'keywords':
                metadata['keywords'] = meta.get('content', '')

        # Perform key phrase extraction
        content_text = content.get_text() if content else ''
        key_phrases = []
        if content_text:
            try:
                documents = [content_text]
                response = text_analytics_client.extract_key_phrases(documents=documents)[0]
                if not response.is_error:
                    key_phrases = response.key_phrases
            except Exception as e:
                logging.error(f"Text Analytics Error: {e}")

        # Build the knowledge graph
        add_to_knowledge_graph(url, header, navigation, content, footer, metadata, key_phrases)

        return func.HttpResponse(
            json.dumps({'message': 'Webpage data processed and stored successfully.'}),
            status_code=200,
            mimetype='application/json'
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)

def add_to_knowledge_graph(url, header, navigation, content, footer, metadata, key_phrases):
    try:
        # Create WebPage vertex
        gremlin_client.submitAsync(f"g.addV('WebPage').property('id', '{url}')").result()

        if header:
            header_content = str(header)[:1000]
            gremlin_client.submitAsync(f"g.addV('Header').property('content', '{header_content}')").result()
            gremlin_client.submitAsync(f"""
                g.V().has('WebPage', 'id', '{url}').addE('hasHeader').to(
                    g.V().has('Header', 'content', '{header_content}')
                )
            """).result()

        if navigation:
            nav_content = str(navigation)[:1000]
            gremlin_client.submitAsync(f"g.addV('Navigation').property('content', '{nav_content}')").result()
            gremlin_client.submitAsync(f"""
                g.V().has('WebPage', 'id', '{url}').addE('hasNavigation').to(
                    g.V().has('Navigation', 'content', '{nav_content}')
                )
            """).result()

        if content:
            content_text = str(content)[:1000]
            gremlin_client.submitAsync(f"g.addV('Content').property('content', '{content_text}')").result()
            gremlin_client.submitAsync(f"""
                g.V().has('WebPage', 'id', '{url}').addE('hasContent').to(
                    g.V().has('Content', 'content', '{content_text}')
                )
            """).result()

            # Add key phrases as entities
            for phrase in key_phrases:
                gremlin_client.submitAsync(f"g.addV('KeyPhrase').property('phrase', '{phrase}')").result()
                gremlin_client.submitAsync(f"""
                    g.V().has('Content', 'content', '{content_text}').addE('hasKeyPhrase').to(
                        g.V().has('KeyPhrase', 'phrase', '{phrase}')
                    )
                """).result()

        if footer:
            footer_content = str(footer)[:1000]
            gremlin_client.submitAsync(f"g.addV('Footer').property('content', '{footer_content}')").result()
            gremlin_client.submitAsync(f"""
                g.V().has('WebPage', 'id', '{url}').addE('hasFooter').to(
                    g.V().has('Footer', 'content', '{footer_content}')
                )
            """).result()

        if metadata:
            for key, value in metadata.items():
                gremlin_client.submitAsync(f"g.V().has('WebPage', 'id', '{url}').property('{key}', '{value}')").result()

    except Exception as e:
        logging.error(f"Error adding to knowledge graph: {e}")
        raise