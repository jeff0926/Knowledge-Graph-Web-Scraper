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

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_text(text):
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_keywords(text, num_keywords=10):
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return [word for word, _ in Counter(words).most_common(num_keywords)]

def calculate_readability_score(text):
    sentences = len(re.findall(r'\w+[.!?]', text))
    words = len(re.findall(r'\w+', text))
    if sentences == 0:
        return 0
    return round((206.835 - 1.015 * (words / sentences) - 84.6 * (sum(1 for word in re.findall(r'\w+', text) if len(word) > 5) / words)), 2)

@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Get the JSON body from the request
        req_body = req.get_json()
        url = req_body.get('url')

        if not url:
            return func.HttpResponse(
                json.dumps({"error": "URL is missing in the request."}),
                mimetype="application/json",
                status_code=400
            )

        if not is_valid_url(url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL provided."}),
                mimetype="application/json",
                status_code=400
            )

        # Fetch the webpage content with a random user agent
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        html_content = response.text

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text-only components
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
            'keywords': ''
        }

        # Extract meta description and keywords
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                metadata['description'] = clean_text(meta.get('content', ''))
            if meta.get('name') == 'keywords':
                metadata['keywords'] = clean_text(meta.get('content', ''))

        # Basic text analysis
        word_count = len(main_text.split())
        
        # Keyword extraction
        keywords = extract_keywords(main_text)

        # Link extraction
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.append({
                'text': link.text.strip(),
                'url': full_url
            })

        # Readability score
        readability_score = calculate_readability_score(main_text)

        # Create a dictionary with all the extracted information
        webpage_data = {
            'url': url,
            'header': header_text[:1000],  # Limit to 1000 characters
            'navigation': nav_text[:1000],
            'content': main_text[:5000],  # Limit to 5000 characters
            'footer': footer_text[:1000],
            'metadata': metadata,
            'word_count': word_count,
            'keywords': keywords,
            'links': links[:20],  # Limit to first 20 links
            'readability_score': readability_score
        }

        # Return the scraped data as JSON response
        return func.HttpResponse(
            json.dumps(webpage_data),
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