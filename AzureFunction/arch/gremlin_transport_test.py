# revised_gremlin_transport_test.py
import gremlin_python
print(f"Gremlin Python package location: {gremlin_python.__file__}")

from gremlin_python.driver import client, serializer
print("Basic gremlin import successful")

print("Available modules in gremlin_python.driver:")
import pkgutil
import gremlin_python.driver as driver
for _, name, _ in pkgutil.iter_modules(driver.__path__):
    print(f"- {name}")

print("\nChecking for specific transports:")
try:
    from gremlin_python.driver.tornado.transport import TornadoTransport
    print("TornadoTransport import successful")
except ImportError as e:
    print(f"TornadoTransport import failed: {e}")

try:
    from gremlin_python.driver.aiohttp.transport import AiohttpTransport
    print("AiohttpTransport import successful")
except ImportError as e:
    print(f"AiohttpTransport import failed: {e}")

try:
    from gremlin_python.driver.transport import AsyncioTransport
    print("AsyncioTransport import successful")
except ImportError as e:
    print(f"AsyncioTransport import failed: {e}")

print("\nChecking other imports:")
import azure.functions as func
print("Azure Functions import successful")

from azure.ai.textanalytics import TextAnalyticsClient
print("Text Analytics import successful")

import requests
print("Requests import successful")

from bs4 import BeautifulSoup
print("BeautifulSoup import successful")

print("\nDetailed Gremlin Python structure:")
import os
gremlin_path = os.path.dirname(gremlin_python.__file__)
for root, dirs, files in os.walk(gremlin_path):
    level = root.replace(gremlin_path, '').count(os.sep)
    indent = ' ' * 4 * (level)
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        print(f"{subindent}{f}")