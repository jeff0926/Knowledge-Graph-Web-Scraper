# test_imports.py
from gremlin_python.driver import client, serializer
print("Basic gremlin import successful")

try:
    from gremlin_python.driver.tornado.transport import TornadoTransport
    print("TornadoTransport import successful")
except ImportError as e:
    print(f"TornadoTransport import failed: {e}")

try:
    from gremlin_python.driver.transport import AsyncioTransport
    print("AsyncioTransport import successful")
except ImportError as e:
    print(f"AsyncioTransport import failed: {e}")

import azure.functions as func
print("Azure Functions import successful")

from azure.ai.textanalytics import TextAnalyticsClient
print("Text Analytics import successful")

import requests
print("Requests import successful")

from bs4 import BeautifulSoup
print("BeautifulSoup import successful")