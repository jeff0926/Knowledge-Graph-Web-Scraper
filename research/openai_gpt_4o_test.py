import requests
import json

# Replace these values with your actual keys and endpoint
AZURE_OPENAI_ENDPOINT = "https://knowledge-graph-openai.openai.azure.com/"  # Provided endpoint
AZURE_OPENAI_API_KEY = "bcc8eb3a8941456e8a2e097bae0b8497"  # Provided API key
DEPLOYMENT_NAME = "gpt-4o"  # Deployment name as given
API_VERSION = "2024-08-01-preview"  # API version to be used

def send_prompt_to_gpt4(prompt):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }

    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

if __name__ == "__main__":
    prompt = (
        "Generate a comprehensive product research document in JSON format following this EXACT structure. Include ALL fields and maintain the EXACT format:\n\n"
        "{\n"
        "  \"metadata\": {\n"
        "    // Include current date, source, query type, category\n"
        "  },\n"
        "  \"summary\": \"Brief overview of the research\",\n"
        "  \"product\": {\n"
        "    // Main product details including aliases and keywords\n"
        "  },\n"
        "  \"resources\": {\n"
        "    // Each resource MUST include:\n"
        "    // - url_metadata (authority_score, content_type, priority)\n"
        "    // - access_info (login requirements, paywall status)\n"
        "    // - content_markers (DOM elements for scraping)\n"
        "    \"product_review_websites\": [\n"
        "      // Major review sites with detailed metadata\n"
        "    ],\n"
        "    \"comparison_websites\": [\n"
        "      // Comparison and testing sites\n"
        "    ],\n"
        "    \"retail_stores\": [\n"
        "      // Major retailers and marketplaces\n"
        "    ],\n"
        "    \"social_media\": [\n"
        "      // Social platforms with relevant content\n"
        "    ]\n"
        "  },\n"
        "  \"top_product\": {\n"
        "    // Details about the most popular/recommended model\n"
        "    // Include pricing and multiple retailers\n"
        "  },\n"
        "  \"search_suggestions\": {\n"
        "    // Related search terms and competitor products\n"
        "  },\n"
        "  \"image_generation\": {\n"
        "    // Detailed prompt for product visualization\n"
        "    // Include style keywords\n"
        "  }\n"
        "}\n\n"
        "Requirements:\n"
        "1. ALL URLs must be real, active websites\n"
        "2. Include authority scores (0.0-1.0) for each source\n"
        "3. Specify content markers for web scraping\n"
        "4. Include access requirements for each source\n"
        "5. Maintain consistent structure across all entries\n"
        "6. Use specific, verifiable product information\n"
        "7. Include comprehensive metadata for each URL\n\n"
        "8. Include the published date of the url/page\n"
        "Generate this structure for the following product/topic: wireless headphones\n\n"
        "The output must be valid JSON and include all specified fields and subfields. Ensure all URLs are properly formatted and all numerical values are appropriate for their context."
    )
    response = send_prompt_to_gpt4(prompt)
    if response:
        print("GPT-4 Response:", response)
