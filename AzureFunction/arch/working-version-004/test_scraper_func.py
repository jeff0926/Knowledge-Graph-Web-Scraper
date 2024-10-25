import requests
import json

def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

url = "http://localhost:8099/api/WebScraperFunction"
data = {"url": "https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/"}
#data = {"url": "https://www.cnn.com/2024/10/11/politics/barack-obama-kamala-harris-analysis/index.html"}
#data = {"url": "https://www.grafdom.com/blog/top-20-best-tech-websites-and-blogs/"}
#data = {"url": "https://daily.dev/blog/top-10-best-tech-websites-and-blogs-2024"}
#data = {"url": "https://www.youtube.com/"}


#https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/
#https://www.cnn.com/2024/10/11/politics/barack-obama-kamala-harris-analysis/index.html
#https://www.grafdom.com/blog/top-20-best-tech-websites-and-blogs/
#https://daily.dev/blog/top-10-best-tech-websites-and-blogs-2024
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(data), headers=headers)


print(f"Status Code: {response.status_code}")
print("Response Headers:")
print(format_json(dict(response.headers)))

print("\nResponse Content:")
print(response.text)

print("\nResponse Content Type:")
print(response.headers.get('Content-Type'))

print("\nResponse Encoding:")
print(response.encoding)

print("\nRaw Response Content:")
print(repr(response.content))

try:
    json_response = response.json()
    print("\nFormatted JSON Response:")
    print(format_json(json_response))
except requests.exceptions.JSONDecodeError as e:
    print(f"\nError decoding JSON: {e}")
    print("Raw response content:")
    print(response.text)

# If the response is HTML, print a part of it
if 'text/html' in response.headers.get('Content-Type', ''):
    print("\nFirst 500 characters of HTML response:")
    print(response.text[:500])