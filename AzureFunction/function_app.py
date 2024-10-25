#
#
#
# Part 1
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
from datetime import datetime
import os

# Import the insertion function from the other file
print("****************** START >> from gremlin_insert_full_json import insert_webpage_data:")
from gremlin_connect_insert_query_full_json import test_gremlin_insert
#from gremlin_connect_insert_query_full_json import insert_webpage_data
print("****************** END  >> from gremlin_insert_full_json import insert_webpage_data:")
# Download necessary NLTK data
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# List of user agents for rotating request headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


def generate_valid_id(url: str) -> str:
    return url.replace("://", "_").replace(".", "_").replace("/", "_")


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
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
# Part 2
#
#
#
#


def process_json_ld(json_ld_data):
    processed_data = []
    for item in json_ld_data:
        if isinstance(item, dict):
            # Process based on @type
            if item.get("@type") == "Article":
                processed_data.append(
                    {
                        "type": "Article",
                        "headline": item.get("headline"),
                        "datePublished": item.get("datePublished"),
                        "author": item.get("author", {}).get("name"),
                    }
                )
            # Add more type-specific processing as needed
    return processed_data


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text


def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return [word for word, _ in Counter(words).most_common(num_keywords)]


def calculate_readability_score(text: str) -> float:
    if not text or not isinstance(text, str):
        return 0.0

    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^a-zA-Z0-9\s.!?]", "", text)

    if not re.search(r"[.!?]", text):
        text += "."

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.split()) > 2]

    if not sentences:
        return 0.0

    text = ". ".join(sentences)
    score = flesch_reading_ease(text)

    return max(0, min(score, 100))


def calculate_word_count(text: str) -> int:
    if not text or not isinstance(text, str):
        return 0

    text = re.sub(r"<[^>]+>", "", text)
    words = [word for word in re.split(r"\s+", text) if word]

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
    og_tags = soup.find_all("meta", property=lambda x: x and x.startswith("og:"))
    for tag in og_tags:
        og_metadata[tag["property"][3:]] = tag.get("content", "")
    return og_metadata


def extract_twitter_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    twitter_metadata = {}
    twitter_tags = soup.find_all(
        "meta", attrs={"name": lambda x: x and x.startswith("twitter:")}
    )
    for tag in twitter_tags:
        twitter_metadata[tag["name"][8:]] = tag.get("content", "")
    return twitter_metadata


def extract_article_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    article_metadata = {}
    article_tags = soup.find_all(
        "meta", property=lambda x: x and x.startswith("article:")
    )
    for tag in article_tags:
        article_metadata[tag["property"][8:]] = tag.get("content", "")
    return article_metadata


def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src:
            full_url = urljoin(base_url, src)
            image_info = {
                "url": full_url,
                "alt": img.get("alt", ""),
                "location": "body",  # Default to body, can be refined later
            }
            images.append(image_info)
    return images


#
#
#
# Part 3
#
#
#
#


@app.route(route="WebScraperFunction")
def WebScraperFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    try:
        req_body = req.get_json()
        url = req_body.get("url")

        if not url or not is_valid_url(url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid or missing URL."}),
                mimetype="application/json",
                status_code=400,
            )

        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")

        images = extract_images(soup, url)

        header = soup.find("header")
        header_text = clean_text(header.get_text()) if header else ""

        nav = soup.find("nav")
        nav_text = clean_text(nav.get_text()) if nav else ""

        main_content = soup.find("main") or soup.find("body")
        main_text = clean_text(main_content.get_text()) if main_content else ""

        footer = soup.find("footer")
        footer_text = clean_text(footer.get_text()) if footer else ""

        metadata = {
            "title": clean_text(soup.title.string) if soup.title else "",
            "description": "",
            "keywords": "",
            "canonical_url": "",
            "author": "",
            "published_time": "",
            "modified_time": "",
            "estimated_reading_time": "",
        }

        for meta in soup.find_all("meta"):
            if meta.get("name") == "description":
                metadata["description"] = clean_text(meta.get("content", ""))
            elif meta.get("name") == "keywords":
                metadata["keywords"] = clean_text(meta.get("content", ""))
            elif meta.get("name") == "author":
                metadata["author"] = clean_text(meta.get("content", ""))

        canonical_tag = soup.find("link", rel="canonical")
        if canonical_tag:
            metadata["canonical_url"] = canonical_tag.get("href", "")

        og_metadata = extract_og_metadata(soup)
        twitter_metadata = extract_twitter_metadata(soup)
        article_metadata = extract_article_metadata(soup)
        structured_data = extract_json_ld(soup)
        processed_json_ld = process_json_ld(structured_data)

        metadata["published_time"] = article_metadata.get("published_time", "")
        metadata["modified_time"] = article_metadata.get("modified_time", "")
        metadata["estimated_reading_time"] = twitter_metadata.get("data2", "")

        social_media_metadata = {"og": og_metadata, "twitter": twitter_metadata}

        word_count = calculate_word_count(main_text)
        keywords = extract_keywords(main_text)
        readability_score = calculate_readability_score(main_text)
        entities = extract_entities(main_text)

        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)
            links.append({"text": link.text.strip(), "url": full_url})

        webpage_data = {
            "id": generate_valid_id(url),
            "url": url,
            "description": metadata["description"],
            "header": header_text[:5000],
            "navigation": nav_text[:5000],
            "content": main_text[:5000],
            "footer": footer_text[:5000],
            "metadata": metadata,
            "social_media_metadata": social_media_metadata,
            "word_count": word_count,
            "keywords": keywords,
            "links": links[:50],
            "readability_score": readability_score,
            "entities": entities,
            "structured_data": structured_data,
            "images": images,
            "processed_json_ld": processed_json_ld,
        }
        output_dir = "output_json"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{generate_valid_id(url)}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(webpage_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Output JSON saved to {output_file}")

        
        # Call the insertion function
        insert_result = insert_webpage_data(webpage_data)

        if insert_result.get("status") == "success":
            logging.info(f"Data inserted into Cosmos DB for URL: {url}")
            webpage_data["verification"] = "Success"
        else:
            logging.error(
                f"Failed to insert data into Cosmos DB: {insert_result.get('error')}"
            )
            webpage_data["verification"] = "Failed"

        return func.HttpResponse(
            json.dumps(webpage_data, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )

    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to fetch the webpage: {str(e)}"}),
            mimetype="application/json",
            status_code=500,
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"An unexpected error occurred: {str(e)}"}),
            mimetype="application/json",
            status_code=500,
        )
