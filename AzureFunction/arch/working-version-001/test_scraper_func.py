import requests
import json

url = "http://localhost:8098/api/WebScraperFunction"
data = {"url": "https://www.cnn.com"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(data), headers=headers)
print(response.status_code)
print(response.json())