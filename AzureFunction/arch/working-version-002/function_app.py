"""
Web Scraper Function

This Azure Function implements a web scraper that extracts content from a given URL.
It performs the following tasks:
1. Validates the input URL
2. Fetches the webpage content
3. Extracts various components (header, navigation, main content, footer)
4. Performs basic text analysis (word count, keyword extraction, readability score)
5. Extracts metadata, social media metadata, and links
6. Performs named entity recognition
7. Returns the scraped and analyzed data in JSON format

The function uses BeautifulSoup for HTML parsing, NLTK for text analysis, and spaCy for named entity recognition.
It includes error handling for invalid URLs and request failures.

Author: [Jeff Conn]
Date: [10.10.24 9:15 pm EST]
Version: 1.1
"""

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

def is_valid_url(url):
    """
    Validates if the given string is a valid URL.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_text(text):
    """
    Cleans the input text by removing extra whitespace and special characters.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_keywords(text, num_keywords=10):
    """
    Extracts the most common keywords from the given text.
    """
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return [word for word, _ in Counter(words).most_common(num_keywords)]


def calculate_readability_score(text):
    sentences = len(re.findall(r'\w+[.!?]', text))
    words = len(re.findall(r'\w+', text))
    if sentences == 0 or words == 0:
        return 0
    avg_sentence_length = words / sentences
    avg_syllables_per_word = sum(count_syllables(word) for word in text.split()) / words
    return round(206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word, 2)

def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count


def extract_entities(text):
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

def extract_og_metadata(soup):
    """
    Extracts Open Graph metadata from the BeautifulSoup object.
    """
    og_metadata = {}
    og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
    for tag in og_tags:
        og_metadata[tag['property'][3:]] = tag.get('content', '')
    return og_metadata

def extract_twitter_metadata(soup):
    """
    Extracts Twitter card metadata from the BeautifulSoup object.
    """
    twitter_metadata = {}
    twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
    for tag in twitter_tags:
        twitter_metadata[tag['name'][8:]] = tag.get('content', '')
    return twitter_metadata

def extract_article_metadata(soup):
    """
    Extracts article-specific metadata from the BeautifulSoup object.
    """
    article_metadata = {}
    article_tags = soup.find_all('meta', property=lambda x: x and x.startswith('article:'))
    for tag in article_tags:
        article_metadata[tag['property'][8:]] = tag.get('content', '')
    return article_metadata

@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function that scrapes a webpage and returns analyzed content.
    """
    logging.info('Python HTTP trigger function processed a request.')

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

        metadata['published_time'] = article_metadata.get('published_time', '')
        metadata['modified_time'] = article_metadata.get('modified_time', '')

        if 'twitter:data2' in twitter_metadata:
            metadata['estimated_reading_time'] = twitter_metadata['data2']

        social_media_metadata = {
            'og': og_metadata,
            'twitter': twitter_metadata
        }

        word_count = len(main_text.split())
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
            'links': links[:20],
            'readability_score': readability_score,
            'entities': entities
        }

        return func.HttpResponse(
            format_json(webpage_data),
            mimetype="application/json",
            status_code=200
)

    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return func.HttpResponse(
            format_json({"error": f"Failed to fetch the webpage: {str(e)}"}),
            mimetype="application/json",
            status_code=500
)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            format_json({"error": f"An unexpected error occurred: {str(e)}"}),
            mimetype="application/json",
            status_code=500
)
    
def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)