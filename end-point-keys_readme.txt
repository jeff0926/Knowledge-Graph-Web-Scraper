# Knowledge-Graph-Web-Scraper Group

This project leverages a web scraper that collects data from the web, organizes it into a knowledge graph, and uses Azure resources for data processing and analysis.

## Azure Resources

### 1. **Azure Cosmos DB (Apache Gremlin)**

- **Account Name:** `knowledgegraph-webscraper-cosmosdb`
- **Resource Group:** `Knowledge-Graph-Web-Scraper_group`
- **Location:** East US
- **API:** Azure Cosmos DB for Apache Gremlin
- **Capacity Mode:** Provisioned throughput
- **Geo-Redundancy:** Disabled
- **Multi-region Writes:** Disabled
- **Availability Zones:** Disabled
- **Subscription:** JC-Core-1
- **Provisioning Event ID:** `Microsoft.Azure.CosmosDB-20241009095759`

### 2. **Azure Cognitive Services (Text Analytics)**

- **Service Name:** `knowledgegraph-webscraper-cognitive-service`
- **Resource Group:** `Knowledge-Graph-Web-Scraper_group`
- **Location:** East US
- **Pricing Tier:** S (1K Calls per minute)
- **Network Access:** Accessible from all networks, including the internet
- **Identity Type:** SystemAssigned (managed identity for the service)
- **Subscription:** JC-Core-1
- **Provisioning Event ID:** `TextAnalyticsCreate-20241009101730`

## Resource Group Information

- **Resource Group Name:** `Knowledge-Graph-Web-Scraper_group`
- **Location:** East US
- **Subscription:** JC-Core-1

### Overview

This group of Azure resources is designed to support a web scraping project that builds a knowledge graph from the data collected. The Cosmos DB service uses the Apache Gremlin API to store and analyze graph data, while the Cognitive Service provides text analytics functionality to process scraped content.

## Features

- **Azure Cosmos DB:** Scalable, globally distributed database designed for graph-based data modeling.
- **Text Analytics:** Powerful cognitive service for natural language processing (NLP) tasks such as sentiment analysis, language detection, and key phrase extraction.
- **Provisioned Throughput:** Ensures performance reliability for high-traffic workloads.
- **SystemAssigned Identity:** Simplifies identity management by automatically managing the credentials of the Azure services involved.

## Licensing

Refer to Microsoft's [Azure Documentation](https://azure.microsoft.com/en-us/documentation/) for more information on pricing, capacity modes, and service availability.

##terminal cmds:

(.venv) PS C:\sandbox\Python\Knowledge-Graph-Web-Scraper\AzureFunction> func start
(.venv) PS C:\sandbox\Python\Knowledge-Graph-Web-Scraper\AzureFunction> func start

C:\sandbox\Python\Knowledge-Graph-Web-Scraper\AzureFunction>C:\sandbox\Python\Knowledge-Graph-Web-Scraper\AzureFunction\.venv\Scripts\activate

(.venv) C:\sandbox\Python\Knowledge-Graph-Web-Scraper\AzureFunction>

Found Python version 3.11.4 (python).



Port 7071 is unavailable. Close the process using that port, or specify another port using --port [-p].
netstat -ano | findstr :7071


this! 
PS C:\sandbox\Python\Knowledge-Graph-Web-Scraper> cd azurefunction
PS C:\sandbox\Python\Knowledge-Graph-Web-Scraper\azurefunction> .venv\Scripts\Activate.ps1
(.venv) PS C:\sandbox\Python\Knowledge-Graph-Web-Scraper\azurefunction> 




