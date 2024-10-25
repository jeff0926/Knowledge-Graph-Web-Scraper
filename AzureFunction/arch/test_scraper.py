# Save this as test_scraper.py
from azure_cosmos_db_noGremline_scrape_json_out_wrx import main, print_status
import os

def test_scraper():
    # Create absolute path for output directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'output_json')
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        print_status(f"Creating output directory at: {output_dir}")
        os.makedirs(output_dir)
    else:
        print_status(f"Output directory already exists at: {output_dir}")

    # Test URL - replace with your target URL
    test_url = "https://apnews.com/article/liam-payne-dies-one-direction-6b7893a56e0d8701096775f611399dd8"
    
    print_status(f"Testing scraper with URL: {test_url}")
    
    try:
        # Run the scraper
        result_path = main(test_url)
        
        if result_path and os.path.exists(result_path):
            print_status(f"Successfully saved JSON to: {result_path}")
            # Verify file size
            file_size = os.path.getsize(result_path)
            print_status(f"File size: {file_size/1024:.2f} KB")
            
            # Verify JSON content (optional)
            import json
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print_status(f"JSON contains {len(data.keys())} top-level keys")
                print_status("Found keys: " + ", ".join(data.keys()))
        else:
            print_status("ERROR: Failed to save JSON file")
            
    except Exception as e:
        print_status(f"ERROR during testing: {str(e)}")

if __name__ == "__main__":
    print_status("Starting scraper test")
    test_scraper()
    print_status("Test completed") 