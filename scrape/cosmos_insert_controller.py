"""
Cosmos DB Insert Controller (cosmos_insert_controller.py)
====================================================

Purpose:
--------
Manages the batch insertion of scraped content into Azure Cosmos DB, ensuring
data persistence and verification while maintaining insertion statistics.

Key Components:
--------------
1. Batch Processing
   - Processes multiple JSON files
   - Maintains processing order
   - Tracks insertion progress

2. Cosmos DB Operations
   - Manages database connections
   - Handles document insertion
   - Verifies successful insertion

3. Status Tracking
   - Maintains insertion statistics
   - Tracks success/failure rates
   - Provides detailed reporting

4. Error Management
   - Handles connection issues
   - Manages insertion failures
   - Provides error reporting

Flow:
-----
1. Scans output_json directory for scraped content
2. For each JSON file:
   - Validates content
   - Inserts into Cosmos DB
   - Verifies insertion
   - Updates statistics
3. Generates processing summary

Configuration:
-------------
- input_dir: Location of JSON files (default: './output_json')
- Uses existing Cosmos DB configuration from web_scrape_cosmos_insert_wrx.py
- Implements processing delays between insertions

Dependencies:
------------
- web_scrape_cosmos_insert_wrx.py: For Cosmos DB operations
- Azure Cosmos DB SDK
- Python stdlib: os, time, logging

Usage:
------
python cosmos_insert_controller.py

Outputs:
1. Console progress updates
2. Final summary report
3. Detailed logging of operations

Integration:
-----------
Final stage of the Knowledge Graph Web Scraper system:
1. Reads from: output_json directory
2. Processes: Scraped content JSONs
3. Inserts into: Azure Cosmos DB

Statistics Tracked:
-----------------
- Total files processed
- Successful insertions
- Failed insertions
- Processing duration
- Error details
"""


import os
import time
import logging
from datetime import datetime
from web_scrape_cosmos_insert_wrx import insert_data_into_cosmosdb, query_data_from_cosmosdb, read_json

class CosmosInsertController:
    def __init__(self, input_dir: str = './output_json'):
        self.input_dir = input_dir
        self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('CosmosInsertController')

    def process_files(self):
        """Process all JSON files in the input directory."""
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'processed_files': []
        }

        try:
            files = [f for f in os.listdir(self.input_dir) if f.endswith('.json')]
            self.logger.info(f"Found {len(files)} JSON files to process")
            
            for filename in files:
                filepath = os.path.join(self.input_dir, filename)
                result = self._process_single_file(filepath)
                
                results['total'] += 1
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    
                results['processed_files'].append({
                    'filename': filename,
                    'success': result['success'],
                    'cosmos_id': result.get('cosmos_id'),
                    'error': result.get('error')
                })
                
                # Brief pause between insertions
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error during batch processing: {str(e)}")
            
        self._print_summary(results)
        return results

    def _process_single_file(self, filepath: str) -> dict:
        """Process a single JSON file."""
        try:
            self.logger.info(f"Processing file: {os.path.basename(filepath)}")
            
            # Read JSON file
            data = read_json(filepath)
            if not data:
                return {'success': False, 'error': 'Failed to read JSON file'}
            
            # Insert into Cosmos DB
            cosmos_id = insert_data_into_cosmosdb(data)
            if not cosmos_id:
                return {'success': False, 'error': 'Failed to insert into Cosmos DB'}
            
            # Verify insertion
            if query_data_from_cosmosdb(cosmos_id):
                return {'success': True, 'cosmos_id': cosmos_id}
            else:
                return {'success': False, 'error': 'Verification failed', 'cosmos_id': cosmos_id}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _print_summary(self, results: dict):
        """Print a summary of the batch processing."""
        self.logger.info("\n" + "="*50)
        self.logger.info("COSMOS DB INSERTION SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Total files processed: {results['total']}")
        self.logger.info(f"Successfully inserted: {results['successful']}")
        self.logger.info(f"Failed insertions: {results['failed']}")
        
        if results['failed'] > 0:
            self.logger.info("\nFailed insertions:")
            for file in results['processed_files']:
                if not file['success']:
                    self.logger.info(f"- {file['filename']}: {file['error']}")
        
        self.logger.info("="*50)

def main():
    controller = CosmosInsertController()
    results = controller.process_files()
    
    # Optional: Archive or move processed files
    # TODO: Add file archiving if needed

if __name__ == "__main__":
    main()