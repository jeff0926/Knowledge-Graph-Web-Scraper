import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse
import logging

class URLQueueManager:
    def __init__(self):
        # Set up directories
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.search_results_dir = os.path.join(self.base_dir, 'output_json')
        self.queue_dir = os.path.join(self.base_dir, 'queue')
        self.queue_file = os.path.join(self.queue_dir, 'queue-list.json')
        
        # Ensure queue directory exists
        os.makedirs(self.queue_dir, exist_ok=True)
        
        # Set up logging
        self._setup_logging()
        
        # Initialize or load queue
        self.queue_data = self._load_queue()

    def _setup_logging(self):
        """Configure logging for the queue manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('url_queue.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('URLQueueManager')

    def _load_queue(self) -> Dict:
        """Load existing queue or create new one."""
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.error(f"Error reading queue file: {self.queue_file}")
                return self._create_new_queue()
        return self._create_new_queue()

    def _create_new_queue(self) -> Dict:
        """Create new queue structure."""
        return {
            "queue_metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_urls": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0
            },
            "urls": []
        }

    def _save_queue(self):
        """Save current queue to file."""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.queue_data, f, indent=2)
            self.logger.info("Queue saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving queue: {str(e)}")

    def _update_metadata(self):
        """Update queue metadata counts."""
        urls = self.queue_data["urls"]
        self.queue_data["queue_metadata"].update({
            "last_updated": datetime.now().isoformat(),
            "total_urls": len(urls),
            "pending": sum(1 for url in urls if url["status"] == "pending"),
            "processing": sum(1 for url in urls if url["status"] == "processing"),
            "completed": sum(1 for url in urls if url["status"] == "completed")
        })

    def read_search_results(self) -> int:
        """
        Read all search result JSONs and add new URLs to queue.
        Returns number of new URLs added.
        """
        new_urls_count = 0
        try:
            for filename in os.listdir(self.search_results_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.search_results_dir, filename)
                self.logger.info(f"Processing search results from: {filename}")
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        search_data = json.load(f)
                    
                    # Extract search term from filename
                    search_term = filename.split('_')[1]  # search_TERM_timestamp.json
                    
                    # Process URLs from search results
                    for url_data in search_data.get("urls", []):
                        if self._add_url_to_queue(url_data, search_term):
                            new_urls_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing {filename}: {str(e)}")
                    continue
            
            self._update_metadata()
            self._save_queue()
            self.logger.info(f"Added {new_urls_count} new URLs to queue")
            return new_urls_count
            
        except Exception as e:
            self.logger.error(f"Error reading search results: {str(e)}")
            return 0

    def _add_url_to_queue(self, url_data: Dict, search_term: str) -> bool:
        """
        Add a URL to the queue if it's not already present.
        Returns True if URL was added, False if it was a duplicate.
        """
        url = url_data.get("url")
        if not url:
            return False
            
        # Check for duplicates
        if any(item["url"] == url for item in self.queue_data["urls"]):
            return False
        
        # Add new URL to queue
        queue_entry = {
            "url": url,
            "priority_score": url_data.get("priority_score", 1.0),
            "source_search": search_term,
            "discovery_date": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.queue_data["urls"].append(queue_entry)
        return True

    def get_next_urls(self, batch_size: int = 5) -> List[str]:
        """Get next batch of pending URLs for processing."""
        pending_urls = [
            url_data for url_data in self.queue_data["urls"]
            if url_data["status"] == "pending"
        ]
        
        # Sort by priority score
        pending_urls.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Get batch and update status
        batch = pending_urls[:batch_size]
        for url_data in batch:
            url_data["status"] = "processing"
        
        self._update_metadata()
        self._save_queue()
        
        return [url_data["url"] for url_data in batch]

    def mark_url_status(self, url: str, status: str):
        """Update status of a specific URL."""
        valid_statuses = {"pending", "processing", "completed", "failed"}
        if status not in valid_statuses:
            self.logger.error(f"Invalid status: {status}")
            return
        
        for url_data in self.queue_data["urls"]:
            if url_data["url"] == url:
                url_data["status"] = status
                url_data["last_updated"] = datetime.now().isoformat()
                break
        
        self._update_metadata()
        self._save_queue()

    def cleanup_queue(self, days_threshold: int = 7):
        """Remove completed URLs older than threshold days."""
        current_time = datetime.now()
        
        def should_keep(url_data):
            if url_data["status"] != "completed":
                return True
                
            completed_date = datetime.fromisoformat(url_data["last_updated"])
            days_old = (current_time - completed_date).days
            return days_old <= days_threshold
        
        original_count = len(self.queue_data["urls"])
        self.queue_data["urls"] = list(filter(should_keep, self.queue_data["urls"]))
        removed_count = original_count - len(self.queue_data["urls"])
        
        if removed_count > 0:
            self._update_metadata()
            self._save_queue()
            self.logger.info(f"Removed {removed_count} old completed URLs")

    def get_queue_stats(self) -> Dict:
        """Get current queue statistics."""
        return {
            "last_updated": self.queue_data["queue_metadata"]["last_updated"],
            "total_urls": self.queue_data["queue_metadata"]["total_urls"],
            "pending": self.queue_data["queue_metadata"]["pending"],
            "processing": self.queue_data["queue_metadata"]["processing"],
            "completed": self.queue_data["queue_metadata"]["completed"],
            "priority_stats": self._calculate_priority_stats()
        }

    def _calculate_priority_stats(self) -> Dict:
        """Calculate priority score statistics."""
        scores = [url_data["priority_score"] for url_data in self.queue_data["urls"]]
        if not scores:
            return {"min": 0, "max": 0, "avg": 0}
        return {
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores)
        }

def main():
    """Example usage of URLQueueManager."""
    manager = URLQueueManager()
    
    # Read new search results
    new_urls = manager.read_search_results()
    print(f"Added {new_urls} new URLs to queue")
    
    # Get queue statistics
    stats = manager.get_queue_stats()
    print("\nQueue Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Get next batch of URLs
    next_urls = manager.get_next_urls(batch_size=3)
    print("\nNext URLs to process:")
    for url in next_urls:
        print(f"- {url}")
    
    # Simulate processing
    for url in next_urls:
        # Simulate some processing time
        time.sleep(1)
        manager.mark_url_status(url, "completed")
    
    # Clean up old entries
    manager.cleanup_queue()

if __name__ == "__main__":
    main()