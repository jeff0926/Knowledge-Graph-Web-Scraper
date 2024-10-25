```markdown
# Knowledge Graph Web Scraper

A Python-based knowledge graph tool that integrates Azure OpenAI (GPT-4O) for research generation and web scraping.

## Setup

### Prerequisites
- Python 3.8 or higher
- Azure subscription with OpenAI access
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/your-username/Knowledge-Graph-Web-Scraper.git
cd Knowledge-Graph-Web-Scraper
```

2. Create and activate virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Azure OpenAI Configuration

1. Required credentials:
```python
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY = "your-api-key"
DEPLOYMENT_NAME = "gpt-4o"  # or your model deployment name
```

2. Place these in your config.py or use environment variables

## Project Structure
```
Knowledge-Graph-Web-Scraper/
├── research/
│   ├── config.py           # Configuration settings
│   ├── research_gen.py     # Research generator
│   └── output_json/        # Generated research files
├── search/
│   └── API_explore/        # API exploration tools
├── requirements.txt
└── README.md
```

## Detailed Usage Examples

### 1. Basic Research Generation
```python
from research.research_gen import ResearchGenerator

# Initialize the generator
generator = ResearchGenerator(
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    deployment_name=DEPLOYMENT_NAME
)

# Single topic research
research_data = generator.generate_research("handheld steamer")

# Multiple topics
topics = ["wireless earbuds", "coffee grinder"]
for topic in topics:
    research = generator.generate_research(topic)
    generator.save_research(research, topic)
```

### 2. Working with Research Results
```python
# Load and validate research
research_data = generator.generate_research("smart watch")
errors = generator.validate_research(research_data)

if not errors:
    # Process valid research
    print(f"Summary: {research_data['summary']}")
    print(f"Top Product: {research_data['top_product']['model']}")
    
    # Access resources
    for website in research_data['resources']['product_review_websites']:
        print(f"Review site: {website['name']} - {website['url']}")
```

### 3. Error Handling
```python
try:
    research_data = generator.generate_research("example topic")
    if research_data:
        filepath = generator.save_research(research_data, "example topic")
        print(f"Research saved to: {filepath}")
    else:
        print("Research generation failed")
except Exception as e:
    print(f"Error: {str(e)}")
```

## Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Issues**
   ```
   Error: 401 Client Error: Unauthorized
   ```
   - Check API key is correct
   - Verify endpoint URL format
   - Ensure deployment name matches Azure setup

2. **Model Deployment Issues**
   ```
   Error: Model 'gpt-4o' not found
   ```
   - Verify model deployment in Azure Portal
   - Check deployment name spelling
   - Ensure model is active

3. **Rate Limiting**
   ```
   Error: 429 Too Many Requests
   ```
   - Implement delays between requests
   - Check quota limits
   - Use batch processing

4. **Environment Setup**
   ```
   ImportError: No module named 'openai'
   ```
   - Verify virtual environment is activated
   - Reinstall requirements
   - Check Python version compatibility

### Solutions

1. **Verify Azure Setup**
```bash
# Test Azure credentials
python -m research.test_connection
```

2. **Check Environment**
```bash
# List installed packages
pip list | grep -E "openai|requests"

# Verify Python version
python --version
```

3. **Reset Environment**
```bash
# Remove and recreate environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Development Guidelines

### 1. Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions
```python
def process_data(input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process input data and return structured results.
    
    Args:
        input_data: Dictionary containing raw input
        
    Returns:
        Processed data dictionary or None if processing fails
    """
    pass
```

### 2. Testing
- Write unit tests for new features
- Run tests before committing
```bash
# Run tests
pytest tests/
```

### 3. Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push changes
git push origin feature/new-feature
```

### 4. Project Organization
- Keep modules focused and small
- Use consistent naming conventions
- Maintain documentation

### 5. Best Practices
- Use environment variables for secrets
- Implement proper error handling
- Add logging for debugging
- Write clear commit messages

### 6. Documentation
- Update README for new features
- Include example usage
- Document configuration changes
- Add inline comments for complex logic

## Features

- Azure OpenAI GPT-4O integration
- Structured research generation
- JSON output format
- Error handling and retries
- File management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```

This extended README includes:
1. Detailed code examples
2. Common troubleshooting scenarios
3. Development best practices
4. Clear project structure
5. Testing guidelines

Would you like me to:
1. Add more specific troubleshooting scenarios?
2. Include additional code examples?
3. Expand any particular section?