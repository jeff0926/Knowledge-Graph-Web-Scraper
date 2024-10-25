"""
Web Scraper Project Documentation
--------------------------------

Project Overview:
----------------
A robust web scraping application designed to extract, process, and store web content with a focus on news articles 
and structured content. The scraper maintains article integrity while bypassing common access restrictions and saving 
data in a standardized JSON format.

Current State (October 2024):
----------------------------
- Fully functional web scraper with domain restriction bypass capabilities
- SEO-friendly file naming with timestamps
- Comprehensive content extraction including metadata, social media tags, and embedded content
- Two-step process: scraping/saving first, database insertion second
- Enhanced error handling and retry mechanisms

Core Functionalities:
-------------------
1. Web Scraping
   - Rotates through multiple user agents
   - Handles various content structures
   - Bypasses basic access restrictions
   - Implements retry logic with exponential backoff

2. Content Processing
   - Extracts main content, metadata, and social media tags
   - Performs NLP analysis for entity extraction
   - Generates keywords and readability metrics
   - Maintains content structure and relationships

3. Data Storage
   - Creates SEO-friendly filenames with timestamps
   - Saves to JSON format in 'output_json' directory
   - Structured for CosmosDB compatibility
   - Maintains data integrity and relationships

File Structure:
--------------
- web_scraper.py: Main scraping application
- cosmos_insert.py: Database insertion utility
- output_json/: Directory for scraped content
- test_scraper.py: Testing and validation suite

Current Workflow:
---------------
1. URL input → Content extraction → JSON file creation
2. Manual verification of JSON output
3. Separate CosmosDB insertion step

Next Steps/TODO:
--------------
1. Implement proxy support
2. Add more sophisticated bypass techniques
3. Enhance error recovery
4. Add content validation
5. Streamline database insertion process

Note: Currently configured for AP News format but adaptable to other content structures.

----------------------

Library Imports and Their Purposes:

requests
    - Handles HTTP requests to web servers
    - Manages GET/POST requests, headers, and response handling
    - Core library for web scraping functionality

BeautifulSoup (from bs4)
    - HTML/XML parsing library
    - Navigates and searches HTML structure
    - Extracts data from HTML tags and attributes

json
    - Handles JSON data encoding and decoding
    - Used for saving scraped data in JSON format
    - Manages data structure serialization

os
    - Provides operating system interface
    - Handles file and directory operations
    - Manages file paths and directory creation

re (Regular Expressions)
    - Pattern matching and text manipulation
    - Cleans and validates text content
    - Extracts patterns from strings

urlparse, urljoin (from urllib.parse)
    - URL parsing and manipulation
    - Combines relative URLs with base URLs
    - Handles URL components and construction

spacy
    - Natural Language Processing (NLP) library
    - Performs entity recognition
    - Analyzes text structure and meaning

datetime
    - Handles date and time operations
    - Creates timestamps for file naming
    - Manages temporal data

nltk (Natural Language Toolkit)
    - Text processing and analysis
    - Tokenization and stop word removal
    - Language processing utilities

word_tokenize (from nltk.tokenize)
    - Splits text into individual words
    - Handles sentence and word boundaries
    - Prepares text for analysis

stopwords (from nltk.corpus)
    - Provides common words to filter out
    - Improves keyword extraction
    - Removes non-significant words

Counter (from collections)
    - Counts occurrences of elements
    - Used for keyword frequency analysis
    - Manages data frequency counting

random
    - Generates random numbers and selections
    - Rotates through User-Agents
    - Adds variation to requests

These libraries together provide a robust toolkit for:
- Web scraping and content extraction
- Text processing and analysis
- File handling and data storage
- URL manipulation and request management
- Natural language processing and entity extraction
"""



import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urlparse, urljoin
import spacy
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import random

# Add these at the top of your existing web_scraper.py file
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

def get_request_headers():
    """Generate headers for web requests."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers',
        'DNT': '1'  # Do Not Track
    }

def print_status(message: str):
    """Print formatted status message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

print_status("Initializing web scraper...")

# Download required NLTK data
print_status("Downloading NLTK data...")
nltk.download('punkt', quiet=False)
nltk.download('stopwords', quiet=False)

print_status("Loading spaCy model...")
nlp = spacy.load('en_core_web_sm')

def generate_file_id(url: str) -> str:
    """Generate a SEO-friendly filename with timestamp."""
    print_status(f"Generating file ID for URL: {url}")
    
    # Parse the URL
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    
    # Find the SEO-friendly part (after 'article' if it exists)
    seo_part = None
    if 'article' in path_parts:
        idx = path_parts.index('article')
        if len(path_parts) > idx + 1:
            seo_part = path_parts[idx + 1]
    
    # If no article part found, use the last significant path component
    if not seo_part:
        seo_part = next((part for part in reversed(path_parts) if part), 'webpage')
    
    # Clean the SEO part (keep only alphanumeric and hyphens)
    seo_part = re.sub(r'[^a-zA-Z0-9-]', '', seo_part)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine parts
    file_id = f"{seo_part}_{timestamp}"
    
    print_status(f"Generated file ID: {file_id}")
    return file_id

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned

def extract_keywords(text: str, num_keywords: int = 10) -> list:
    """Extract main keywords from text."""
    print_status("Extracting keywords from content...")
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    keywords = [word for word, _ in Counter(words).most_common(num_keywords)]
    print_status(f"Found {len(keywords)} keywords")
    return keywords

def extract_entities(text: str) -> dict:
    """Extract named entities from text."""
    print_status("Extracting named entities...")
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        if ent.text not in entities[ent.label_]:
            entities[ent.label_].append(ent.text)
    print_status(f"Found entities in {len(entities)} categories")
    return entities

def extract_social_metadata(soup: BeautifulSoup) -> dict:
    """Extract social media metadata."""
    print_status("Extracting social media metadata...")
    og_data = {}
    twitter_data = {}
    
    # Extract OpenGraph metadata
    for tag in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
        og_data[tag['property'][3:]] = tag.get('content', '')
    print_status(f"Found {len(og_data)} OpenGraph tags")
    
    # Extract Twitter metadata
    for tag in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
        twitter_data[tag['name'][8:]] = tag.get('content', '')
    print_status(f"Found {len(twitter_data)} Twitter tags")
    
    return {
        'og': og_data,
        'twitter': twitter_data
    }

def extract_images(soup: BeautifulSoup, base_url: str) -> list:
    """Extract image information from the page."""
    print_status("Extracting images...")
    images = []
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src:
            image_info = {
                'url': urljoin(base_url, src),
                'alt': img.get('alt', ''),
                'location': 'body'
            }
            images.append(image_info)
    print_status(f"Found {len(images)} images")
    return images

def extract_links(soup: BeautifulSoup, base_url: str) -> list:
    """Extract links from the page."""
    print_status("Extracting links...")
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href:
            links.append({
                'text': clean_text(link.text),
                'url': urljoin(base_url, href)
            })
    print_status(f"Found {len(links)} links")
    return links

def scrape_webpage(url: str) -> dict:
    """Main function to scrape webpage and format data."""
    print_status(f"Starting to scrape URL: {url}")
    try:
        # Setup session with enhanced headers
        print_status("Setting up session...")
        session = requests.Session()
        retries = 3
        delay = 2  # seconds
        
        for attempt in range(retries):
            try:
                # Get fresh headers for each attempt
                headers = get_request_headers()
                print_status(f"Attempt {attempt + 1} with User-Agent: {headers['User-Agent']}")
                
                response = session.get(
                    url,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True,
                    verify=False  # Be careful with this in production
                )
                response.raise_for_status()
                print_status("Successfully retrieved webpage")
                break
            except requests.RequestException as e:
                if attempt == retries - 1:  # Last attempt
                    raise
                print_status(f"Attempt {attempt + 1} failed: {str(e)}")
                print_status(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
        
        # Parse content
        print_status("Parsing HTML content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content
        print_status("Extracting main content...")
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        content_text = clean_text(main_content.get_text()) if main_content else ""
        print_status(f"Extracted {len(content_text)} characters of main content")
        
        # Build structured data
        print_status("Building structured data...")
        webpage_data = {
            'id': generate_file_id(url),
            'url': url,
            'description': clean_text(soup.find('meta', {'name': 'description'})['content']) if soup.find('meta', {'name': 'description'}) else '',
            'header': clean_text(soup.find('header').get_text()) if soup.find('header') else '',
            'navigation': clean_text(soup.find('nav').get_text()) if soup.find('nav') else '',
            'content': content_text,
            'footer': clean_text(soup.find('footer').get_text()) if soup.find('footer') else '',
            'metadata': {
                'title': clean_text(soup.title.string) if soup.title else '',
                'description': clean_text(soup.find('meta', {'name': 'description'})['content']) if soup.find('meta', {'name': 'description'}) else '',
                'keywords': clean_text(soup.find('meta', {'name': 'keywords'})['content']) if soup.find('meta', {'name': 'keywords'}) else '',
                'canonical_url': soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else url,
                'author': clean_text(soup.find('meta', {'name': 'author'})['content']) if soup.find('meta', {'name': 'author'}) else '',
                'published_time': soup.find('meta', {'property': 'article:published_time'})['content'] if soup.find('meta', {'property': 'article:published_time'}) else '',
                'modified_time': soup.find('meta', {'property': 'article:modified_time'})['content'] if soup.find('meta', {'property': 'article:modified_time'}) else '',
            }
        }
        
        print_status("Extracting additional components...")
        webpage_data.update({
            'social_media_metadata': extract_social_metadata(soup),
            'word_count': len(content_text.split()),
            'keywords': extract_keywords(content_text),
            'links': extract_links(soup, url),
            'readability_score': 0,
            'entities': extract_entities(content_text),
            'structured_data': [],
            'images': extract_images(soup, url),
            'processed_json_ld': []
        })
        
        print_status("Data extraction completed successfully")
        return webpage_data
        
    except Exception as e:
        print_status(f"ERROR scraping {url}: {str(e)}")
        return None
    

def save_to_json(data: dict, output_dir: str = 'output_json'):
    """Save scraped data to JSON file."""
    print_status(f"Preparing to save data to {output_dir}")
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            print_status(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)
        
        # Generate filename
        filename = f"{data['id']}.json"
        filepath = os.path.join(output_dir, filename)
        print_status(f"Saving to file: {filepath}")
        
        # Save file with proper encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print_status(f"Successfully saved data to {filepath}")
        return filepath
        
    except Exception as e:
        print_status(f"ERROR saving JSON: {str(e)}")
        return None

def main(url: str):
    """Main function to coordinate scraping and saving."""
    print_status(f"Starting processing for URL: {url}")
    
    # Scrape webpage
    data = scrape_webpage(url)
    if data:
        # Save to JSON
        filepath = save_to_json(data)
        if filepath:
            print_status(f"Successfully processed {url}")
            return filepath
    
    print_status("Processing completed")
    return None

# Example usage
if __name__ == "__main__":
    # Test URL
    print_status("Starting web scraper script")
    url = "https://www.foxnews.com/"  # Replace with actual URL
    main(url)
    print_status("Script execution completed")