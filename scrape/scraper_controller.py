"""
Scraper Controller (scraper_controller.py)
========================================

Purpose:
--------
Orchestrates the web scraping process by integrating the URL queue manager with the
web scraper. Acts as a bridge between queue management and content extraction.

Key Components:
--------------
1. URL Queue Integration
   - Pulls URLs from queue manager in configurable batch sizes
   - Updates URL status (processing, completed, failed)
   - Maintains queue synchronization

2. Scraping Orchestration
   - Controls web_scraper_wrx.py execution
   - Manages batch processing
   - Implements retry logic for failed attempts

3. Error Handling
   - Implements exponential backoff for retries
   - Logs failures and exceptions
   - Maintains system state during errors

4. Resource Management
   - Controls batch sizes
   - Implements processing delays
   - Manages system resources

Flow:
-----
1. Initializes connection to URL queue
2. Retrieves batch of pending URLs
3. For each URL:
   - Attempts scraping with retries
   - Saves scraped content
   - Updates URL status
4. Continues until queue is empty or stopped

Configuration:
-------------
- batch_size: Number of URLs to process in each batch (default: 5)
- max_retries: Maximum retry attempts per URL (default: 3)
- delay: Time between batch processing (default: 60 seconds)

Dependencies:
------------
- url_queue.py: For queue management
- web_scraper_wrx.py: For content scraping
- Python stdlib: os, sys, time, logging

Usage:
------
python scraper_controller.py

The controller can run in two modes:
1. Single batch mode: Process one batch and exit
2. Continuous mode: Keep processing until queue is empty

Integration:
-----------
Part of the Knowledge Graph Web Scraper system:
1. Reads from: URL queue (queue-list.json)
2. Uses: web_scraper_wrx.py for scraping
3. Produces: Scraped content JSONs in output_json/
"""


import os
import sys
import time
from datetime import datetime
import logging
from typing import List, Optional

# Add parent directory to path to import queue manager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from search.url_queue import URLQueueManager

# Import your existing scraper
from web_scraper_wrx import scrape_webpage, save_to_json

class ScraperController:
    def __init__(self, batch_size: int = 5, max_retries: int = 3):
        self.queue_manager = URLQueueManager()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the scraper controller."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper_controller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ScraperController')

    def process_batch(self) -> bool:
        """
        Process a batch of URLs from the queue.
        Returns True if URLs were processed, False if queue is empty.
        """
        # Get next batch of URLs from queue
        urls = self.queue_manager.get_next_urls(batch_size=self.batch_size)
        
        if not urls:
            self.logger.info("No pending URLs in queue")
            return False

        self.logger.info(f"Processing batch of {len(urls)} URLs")
        
        for url in urls:
            self._process_single_url(url)
            
        return True

    def _process_single_url(self, url: str):
        """Process a single URL with retries."""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Processing URL: {url} (Attempt {attempt + 1}/{self.max_retries})")
                
                # Use your existing scraper function
                scraped_data = scrape_webpage(url)
                
                if scraped_data:
                    # Save using your existing function
                    filepath = save_to_json(scraped_data)
                    
                    if filepath:
                        self.logger.info(f"Successfully scraped and saved: {url}")
                        self.queue_manager.mark_url_status(url, "completed")
                        return
                
                self.logger.error(f"Failed to scrape URL: {url}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Error processing {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    self.queue_manager.mark_url_status(url, "failed")
                time.sleep(2 ** attempt)

    def run(self, continuous: bool = False, delay: int = 60):
        """
        Run the scraper controller.
        
        Args:
            continuous: If True, keep running until queue is empty
            delay: Delay in seconds between batches when running continuously
        """
        self.logger.info("Starting scraper controller")
        
        while True:
            # Process any new search results
            new_urls = self.queue_manager.read_search_results()
            if new_urls > 0:
                self.logger.info(f"Added {new_urls} new URLs to queue")
            
            # Process a batch
            if not self.process_batch():
                if not continuous:
                    break
                self.logger.info(f"Queue empty, waiting {delay} seconds...")
                time.sleep(delay)
                continue
            
            if not continuous:
                break
            
            time.sleep(delay)
        
        self.logger.info("Scraper controller finished")

def main():
    """Example usage of ScraperController."""
    # Initialize controller
    controller = ScraperController(
        batch_size=5,
        max_retries=3
    )
    
    # Print initial queue stats
    stats = controller.queue_manager.get_queue_stats()
    print("\nInitial Queue Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Run the controller
    print("\nStarting scraping process...")
    controller.run(
        continuous=True,  # Keep running until queue is empty
        delay=60         # Wait 60 seconds between batches
    )

if __name__ == "__main__":
    main()