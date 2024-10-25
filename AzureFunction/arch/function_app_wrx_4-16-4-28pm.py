#
#
#
#Part 1
#
#
#
#

import logging
import azure.functions as func
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, urljoin
import random
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from textstat import flesch_reading_ease
from typing import List, Dict, Any
from gremlin_python.driver import client, serializer
import asyncio
from datetime import datetime

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# List of user agents for rotating request headers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# Cosmos DB configuration
COSMOS_DB_ENDPOINT = 'wss://knowledgegraph-webscraper-cosmosdb.gremlin.cosmos.azure.com:443/'
COSMOS_DB_KEY = 'fsN0JHBIeYxCqvvD29VP256jS6NpJsJn5mnewiwkn4k3M6hQeCzbyuXeO9dnMWizJMGXd5fiCsSIACDbyi4SKA=='
DATABASE = 'WebScraperDB'
GRAPH = 'WebPages'

#------10.16.11:50----->>>>>
def generate_valid_id(url: str) -> str:
    return url.replace("://", "_").replace(".", "_").replace("/", "_")


def create_gremlin_client():
    return client.Client(
        COSMOS_DB_ENDPOINT,
        'g',
        username=f"/dbs/WebScraperDB/colls/Webpages",
        password=COSMOS_DB_KEY,
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

async def insert_webpage_data(gremlin_client, webpage_data):
    try:
        # Escape single quotes in the URL, title, and content to prevent Gremlin syntax errors
        safe_url = webpage_data['url'].replace("'", "\\'")
        safe_title = webpage_data['metadata']['title'].replace("'", "\\'")
        safe_content = webpage_data['content'][:1000].replace("'", "\\'")  # Limit content size and escape

 #------10.16.11:50----->>>>>          
        safe_metadata = json.dumps(webpage_data['metadata']).replace("'", "\\'")
        safe_analysis = json.dumps(webpage_data['analysis']).replace("'", "\\'")
        safe_social_media = json.dumps(webpage_data['social_media_metadata']).replace("'", "\\'")
        safe_structured_data = json.dumps(webpage_data['structured_data']).replace("'", "\\'")
        safe_images = json.dumps(webpage_data['images']).replace("'", "\\'")
        safe_links = json.dumps(webpage_data['links'][:50]).replace("'", "\\'")  # Limit to 50 links

 #------10.16.11:50----->>>>>       
        valid_id = generate_valid_id(webpage_data['url']) # Generate a valid ID


        # Create vertex
        query = (
            "g.addV('WebPage')"
            f".property('id', '{valid_id}')"
            f".property('url', '{safe_url}')"
            f".property('title', '{safe_title}')"
            f".property('content', '{safe_content}')"
            f".property('metadata', '{safe_metadata}')"
            f".property('analysis', '{safe_analysis}')"
            f".property('social_media_metadata', '{safe_social_media}')"
            f".property('structured_data', '{safe_structured_data}')"
            f".property('images', '{safe_images}')"
            f".property('links', '{safe_links}')"
            f".property('scrapeDate', '{datetime.now().isoformat()}')"
        )
        await gremlin_client.submitAsync(query)


#------10.16.11:50----->>>>>  
        # Create edges for keywords (limit to top 5 for efficiency)
        for keyword in webpage_data['analysis']['keywords'][:5]:  # Limit to top 5 keywords
            safe_keyword = keyword.replace("'", "\\'")
            keyword_id = generate_valid_id(f"keyword_{safe_keyword}")
            query = (
                f"g.V('{valid_id}').as('webpage')"
                f".coalesce(g.V('{keyword_id}'), "
                f"addV('Keyword').property('id', '{keyword_id}').property('keyword', '{safe_keyword}'))"
                f".as('keyword')"
                ".coalesce(__.inE('HAS_KEYWORD').where(outV().as('webpage')), addE('HAS_KEYWORD').from('webpage'))"
            )
            await gremlin_client.submitAsync(query)

        print(f"Data inserted for {webpage_data['url']}")
    except Exception as e:
        print(f"Error inserting data: {e}")

def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    structured_data = []

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except json.JSONDecodeError as e:
            logging.warning(f"Error decoding JSON-LD: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error processing JSON-LD: {str(e)}")

    return structured_data
#
#
#
#Part 2
#
#
#
#

def process_json_ld(json_ld_data):
    processed_data = []
    for item in json_ld_data:
        if isinstance(item, dict):
            # Process based on @type
            if item.get('@type') == 'Article':
                processed_data.append({
                    'type': 'Article',
                    'headline': item.get('headline'),
                    'datePublished': item.get('datePublished'),
                    'author': item.get('author', {}).get('name')
                })
            # Add more type-specific processing as needed
    return processed_data

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return [word for word, _ in Counter(words).most_common(num_keywords)]

def calculate_readability_score(text: str) -> float:
    if not text or not isinstance(text, str):
        return 0.0
    
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^a-zA-Z0-9\s.!?]', '', text)
    
    if not re.search(r'[.!?]', text):
        text += '.'
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.split()) > 2]
    
    if not sentences:
        return 0.0
    
    text = '. '.join(sentences)
    score = flesch_reading_ease(text)
    
    return max(0, min(score, 100))

def calculate_word_count(text: str) -> int:
    if not text or not isinstance(text, str):
        return 0
    
    text = re.sub(r'<[^>]+>', '', text)
    words = [word for word in re.split(r'\s+', text) if word]
    
    return len(words)

def extract_entities(text: str) -> Dict[str, List[str]]:
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)
    return entities

def extract_og_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    og_metadata = {}
    og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
    for tag in og_tags:
        og_metadata[tag['property'][3:]] = tag.get('content', '')
    return og_metadata

def extract_twitter_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    twitter_metadata = {}
    twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
    for tag in twitter_tags:
        twitter_metadata[tag['name'][8:]] = tag.get('content', '')
    return twitter_metadata

def extract_article_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    article_metadata = {}
    article_tags = soup.find_all('meta', property=lambda x: x and x.startswith('article:'))
    for tag in article_tags:
        article_metadata[tag['property'][8:]] = tag.get('content', '')
    return article_metadata

def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    images = []
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            image_info = {
                'url': full_url,
                'alt': img.get('alt', ''),
                'location': 'body'  # Default to body, can be refined later
            }
            images.append(image_info)
    return images

def prepare_for_cosmos_db(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": data['url'],
        "url": data['url'],
        "metadata": data['metadata'],
        "content": {
            "header": data['header'],
            "navigation": data['navigation'],
            "body": data['content'],
            "footer": data['footer']
        },
        "images": data['images'],
        "analysis": {
            "word_count": data['word_count'],
            "readability_score": round(data['readability_score'], 2),
            "keywords": data['keywords'],
            "entities": data['entities']
        },
        "links": data['links'],
        "social_media_metadata": data['social_media_metadata'],
        "structured_data": data.get('structured_data', []),
        "processed_json_ld": data.get('processed_json_ld', [])
    }
#
#
#
#Part 3
#
#
#
#

@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    webpage_data = {}
    gremlin_client = None

    try:
        gremlin_client = create_gremlin_client()
             
        req_body = req.get_json()
        url = req_body.get('url')

        if not url or not is_valid_url(url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid or missing URL."}),
                mimetype="application/json",
                status_code=400
            )

        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        images = extract_images(soup, url)

        header = soup.find('header')
        header_text = clean_text(header.get_text()) if header else ''

        nav = soup.find('nav')
        nav_text = clean_text(nav.get_text()) if nav else ''

        main_content = soup.find('main') or soup.find('body')
        main_text = clean_text(main_content.get_text()) if main_content else ''

        footer = soup.find('footer')
        footer_text = clean_text(footer.get_text()) if footer else ''

        metadata = {
            'title': clean_text(soup.title.string) if soup.title else '',
            'description': '',
            'keywords': '',
            'canonical_url': '',
            'author': '',
            'published_time': '',
            'modified_time': '',
            'estimated_reading_time': ''
        }

        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                metadata['description'] = clean_text(meta.get('content', ''))
            elif meta.get('name') == 'keywords':
                metadata['keywords'] = clean_text(meta.get('content', ''))
            elif meta.get('name') == 'author':
                metadata['author'] = clean_text(meta.get('content', ''))

        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag:
            metadata['canonical_url'] = canonical_tag.get('href', '')

        og_metadata = extract_og_metadata(soup)
        twitter_metadata = extract_twitter_metadata(soup)
        article_metadata = extract_article_metadata(soup)
        structured_data = extract_json_ld(soup)
        processed_json_ld = process_json_ld(structured_data)

        metadata['published_time'] = article_metadata.get('published_time', '')
        metadata['modified_time'] = article_metadata.get('modified_time', '')
        metadata['estimated_reading_time'] = twitter_metadata.get('data2', '')

        social_media_metadata = {
            'og': og_metadata,
            'twitter': twitter_metadata
        }

        word_count = calculate_word_count(main_text)
        keywords = extract_keywords(main_text)
        readability_score = calculate_readability_score(main_text)
        entities = extract_entities(main_text)

        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.append({
                'text': link.text.strip(),
                'url': full_url
            })

        webpage_data = {
            'url': url,
            'description': metadata['description'],
            'header': header_text[:5000],
            'navigation': nav_text[:5000],
            'content': main_text[:5000],
            'footer': footer_text[:5000],
            'metadata': metadata,
            'social_media_metadata': social_media_metadata,
            'word_count': word_count,
            'keywords': keywords,
            'links': links[:50],
            'readability_score': readability_score,
            'entities': entities,
            'structured_data': structured_data,
            'images': images,
            'processed_json_ld': processed_json_ld
        }

        cosmos_db_document = prepare_for_cosmos_db(webpage_data)

        try:
            asyncio.get_event_loop().run_until_complete(insert_webpage_data(gremlin_client, cosmos_db_document))
            logging.info(f"Data inserted into Cosmos DB for URL: {url}")
            #------10.16.11:50----->>>>>  
            valid_id = generate_valid_id(cosmos_db_document['url'])
            
            verify_query = f"g.V('{cosmos_db_document['url']}').valueMap()"
            result = asyncio.get_event_loop().run_until_complete(gremlin_client.submitAsync(verify_query))
            verification_result = result.all().result()

            if verification_result:
                logging.info(f"Data verified in Cosmos DB for URL: {cosmos_db_document['url']}")
                cosmos_db_document['verification'] = "Success"
                logging.info(f"Verification result: {json.dumps(verification_result)}")
            else:
                logging.warning(f"Data not found in Cosmos DB for URL: {cosmos_db_document['url']}")
                cosmos_db_document['verification'] = "Failed"

        except Exception as e:
            logging.error(f"Failed to insert or verify data in Cosmos DB: {str(e)}")
            cosmos_db_document['verification'] = "Error"

        return func.HttpResponse(
            json.dumps(cosmos_db_document, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to fetch the webpage: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"An unexpected error occurred: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
    finally:
        if gremlin_client:
            gremlin_client.close()
#def format_json(data):
    #return json.dumps(data, indent=2, ensure_ascii=False)