C:\sandbox\Python\Knowledge-Graph-Web-Scraper\scrape

Directories:
/health/
- Purpose: Contains health check scripts and logs
- Used for: Monitoring system status and component connectivity
- Important for: System reliability and monitoring

/mermaid/
- Purpose: Stores Mermaid diagram files
- Used for: System architecture and flow documentation
- Contains: Visual representations of system workflows

/output_json/
- Purpose: Storage for scraped content
- Used for: Temporary storage between scraping and DB insertion
- Contains: JSON files from web scraping operations

/**pycache**/
- Purpose: Python's bytecode cache
- Used for: Improving load times of Python modules
- Note: Not part of version control, automatically generated

Core Files:
cosmos_insert_controller.py (5,969 bytes)
- Purpose: Manages Cosmos DB insertions
- Key Feature: Batch processing of scraped content
- Last Updated: Most recent (4:50 PM)

scraper_controller.py (6,652 bytes)
- Purpose: Orchestrates web scraping operations
- Key Feature: Integrates queue and scraper
- Last Updated: Most recent (4:50 PM)

web_scraper_wrx.py (16,474 bytes)
- Purpose: Core scraping functionality
- Key Feature: Content extraction and processing
- Last Updated: Morning update (11:15 AM)

web_scrape_cosmos_insert_wrx.py (5,504 bytes)
- Purpose: Cosmos DB interaction logic
- Key Feature: Database operations
- Last Updated: Morning update (11:21 AM)

Log Files:
scraper_controller.log (0 bytes)
- Purpose: Logs scraper controller operations
- Status: New/empty file
- Used for: Debugging and monitoring scraping

url_queue.log (39,250 bytes)
- Purpose: Logs queue operations
- Status: Active with substantial logging
- Used for: URL processing tracking