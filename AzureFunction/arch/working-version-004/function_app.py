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


import os
#from azure.cosmos import CosmosClient, PartitionKey

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
    """
    Validates if the given string is a valid URL.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_text(text: str) -> str:
    """
    Cleans the input text by removing extra whitespace and special characters.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
    """
    Extracts the most common keywords from the given text.
    """
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return [word for word, _ in Counter(words).most_common(num_keywords)]

def calculate_readability_score(text: str) -> float:
    if not text or not isinstance(text, str):
        return 0.0
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Keep alphanumeric characters, periods, question marks, exclamation points, and spaces
    text = re.sub(r'[^a-zA-Z0-9\s.!?]', '', text)
    
    # Ensure there's at least one sentence-ending punctuation
    if not re.search(r'[.!?]', text):
        text += '.'
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    
    # Filter out empty sentences and very short sentences (less than 3 words)
    sentences = [s.strip() for s in sentences if len(s.split()) > 2]
    
    if not sentences:
        return 0.0
    
    # Rejoin the text
    text = '. '.join(sentences)
    
    score = flesch_reading_ease(text)
    
    # Clamp the score between 0 and 100
    return max(0, min(score, 100))

def calculate_word_count(text: str) -> int:
    """
    Calculates the word count of the given text, handling HTML tags and multiple whitespace characters.
    """
    if not text or not isinstance(text, str):
        return 0
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Split on whitespace and filter out empty strings
    words = [word for word in re.split(r'\s+', text) if word]
    
    return len(words)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extracts named entities from the given text using spaCy.
    """
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)
    return entities

def extract_og_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts Open Graph metadata from the BeautifulSoup object.
    """
    og_metadata = {}
    og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
    for tag in og_tags:
        og_metadata[tag['property'][3:]] = tag.get('content', '')
    return og_metadata

def extract_twitter_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts Twitter card metadata from the BeautifulSoup object.
    """
    twitter_metadata = {}
    twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
    for tag in twitter_tags:
        twitter_metadata[tag['name'][8:]] = tag.get('content', '')
    return twitter_metadata

def extract_article_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts article-specific metadata from the BeautifulSoup object.
    """
    article_metadata = {}
    article_tags = soup.find_all('meta', property=lambda x: x and x.startswith('article:'))
    for tag in article_tags:
        article_metadata[tag['property'][8:]] = tag.get('content', '')
    return article_metadata

def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Extracts JSON-LD structured data from the BeautifulSoup object.
    """
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    structured_data = []

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except json.JSONDecodeError:
            continue

    return structured_data



def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """
    Extracts image information from the BeautifulSoup object.
    """
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
        "images": data['images'],  # Add the new images field
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

@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function that scrapes a webpage and returns analyzed content.
    """
    logging.info('Python HTTP trigger function processed a request.')

    webpage_data = {}  # Initialize webpage_data here
    

    try:
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

        # Extract images
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
        # This should go after the line: structured_data = extract_json_ld(soup)
        processed_json_ld = process_json_ld(structured_data)
        webpage_data['processed_json_ld'] = processed_json_ld

        metadata['published_time'] = article_metadata.get('published_time', '')
        metadata['modified_time'] = article_metadata.get('modified_time', '')

        if 'twitter:data2' in twitter_metadata:
            metadata['estimated_reading_time'] = twitter_metadata['data2']

        social_media_metadata = {
            'og': og_metadata,
            'twitter': twitter_metadata
        }

        word_count = calculate_word_count(main_text)
        keywords = extract_keywords(main_text)
        readability_score = calculate_readability_score(main_text)
        logging.info(f"Readability score: {readability_score}")  # Add this line for debugging
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
            'links': links[:20],
            'readability_score': readability_score,
            'entities': entities,
            'structured_data': structured_data,
            'images': images  # Add the extracted images
        }

        # Prepare data for Cosmos DB
        cosmos_db_document = prepare_for_cosmos_db(webpage_data)

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
#def format_json(data):
    #return json.dumps(data, indent=2, ensure_ascii=False)