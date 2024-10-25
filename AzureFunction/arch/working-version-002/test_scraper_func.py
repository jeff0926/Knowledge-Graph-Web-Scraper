import requests
import json

def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

url = "http://localhost:8098/api/WebScraperFunction"
data = {"url": "https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/"}
#https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/
#https://www.cnn.com/2024/10/11/politics/barack-obama-kamala-harris-analysis/index.html
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(data), headers=headers)
print(response.status_code)
print(format_json(response.json()))