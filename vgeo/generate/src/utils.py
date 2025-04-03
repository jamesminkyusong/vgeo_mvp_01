import json
import asyncio

from tavily import TavilyClient, AsyncTavilyClient
from langsmith import traceable

tavily_client = TavilyClient()
tavily_async_client = AsyncTavilyClient()

def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=True):
    """
    Processes Tavily web search results, deduplicates them, and formats them for use.

    Args:
        search_response (dict or list): Raw search results from Tavily.
        max_tokens_per_source (int): Max number of tokens per source.
        include_raw_content (bool): Whether to include raw content from sources.

    Returns:
        tuple: (formatted_text, full_documents)
            - formatted_text (str): Human-readable text summarizing sources.
            - full_documents (list[dict]): List of structured document metadata.
    """
    # Convert input to list of results
    if isinstance(search_response, dict):
        sources_list = search_response.get('results', [])
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")

    # Deduplicate by URL
    unique_sources = {}
    full_documents = []
    
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source

    # Format output
    formatted_text = "Web Search Results (Tavily):\n\n"
    
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {i}: {source['title']}\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"

        # Handle optional raw content
        raw_content = source.get('raw_content', '')
        char_limit = max_tokens_per_source * 4  # Approximate character-to-token conversion

        if include_raw_content and raw_content:
            raw_content = raw_content[:char_limit] + ("... [truncated]" if len(raw_content) > char_limit else "")
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"

        # Store structured document metadata
        full_documents.append({
            "title": source.get('title', 'Unknown Title'),
            "url": source.get('url', 'N/A'),
            "content": source.get('content', ''),
            "source_type": "Tavily",
            "raw_content": raw_content
        })

    return formatted_text.strip(), full_documents


def deduplicate_and_format_milvus_sources(milvus_docs, max_tokens_per_source=1000):
    """
    Processes and formats retrieved documents from Milvus vector search.

    Args:
        milvus_docs (list): List of retrieved documents from Milvus.
        max_tokens_per_source (int): Max number of tokens per document.

    Returns:
        tuple: (formatted_text, full_documents)
            - formatted_text (str): Human-readable summary of Milvus results.
            - full_documents (list[dict]): List of structured document metadata.
    """
    if not milvus_docs:
        return "No relevant vector search results found.", []

    # Deduplicate based on unique document content
    unique_texts = set()
    formatted_text = "Vector Search Results (Milvus):\n\n"
    full_documents = []

    for i, doc in enumerate(milvus_docs, 1):
        content = doc.page_content.strip()
        
        if content not in unique_texts:
            unique_texts.add(content)

            # Truncate content to the token limit
            char_limit = max_tokens_per_source * 4
            truncated_content = content[:char_limit] + ("... [truncated]" if len(content) > char_limit else "")

            formatted_text += f"Source {i}:\n===\n"
            formatted_text += f"{truncated_content}\n\n"

            # Store structured document metadata
            full_documents.append({
                "title": doc.metadata.get("title", f"Milvus Document {i}"),
                "source_type": "Vector",
                "content": content,
                "truncated_content": truncated_content
            })

    return formatted_text.strip(), full_documents



@traceable
def tavily_search(query):
    """ Search the web using the Tavily API.
    
    Args:
        query (str): The search query to execute
        
    Returns:
        dict: Tavily search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the search result
                - url (str): URL of the search result
                - content (str): Snippet/summary of the content
                - raw_content (str): Full content of the page if available"""
     
    return tavily_client.search(query, 
                         max_results=3, 
                         include_raw_content=True)

@traceable
async def tavily_search_async(search_queries, tavily_topic, tavily_days):
    """
    Performs concurrent web searches using the Tavily API.

    Args:
        search_queries (List[SearchQuery]): List of search queries to process
        tavily_topic (str): Type of search to perform ('news' or 'general')
        tavily_days (int): Number of days to look back for news articles (only used when tavily_topic='news')

    Returns:
        List[dict]: List of search results from Tavily API, one per query

    Note:
        For news searches, each result will include articles from the last `tavily_days` days.
        For general searches, the time range is unrestricted.
    """
    
    search_tasks = []
    for query in search_queries:
        if tavily_topic == "news":
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=2,
                    include_raw_content=True,
                    topic="news",
                    days=tavily_days
                )
            )
        else:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=2,
                    include_raw_content=True,
                    topic="general"
                )
            )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)
    return search_docs

def format_selected_scenarios(scenario_df):
    records = scenario_df.to_dict(orient='records')
    return json.dumps(records, indent=2)

def format_cluster_info(cluster_info_df):
    cluster_info_df.columns = ['cluster_ID', 'cluster_description']
    cluster_descriptions = []
    cluster_info_df
    for idx, row in cluster_info_df.iterrows():
        cluster_ID = row['cluster_ID']    
        desc = row['cluster_description']
        formatted_txt = f"Cluster_ID: {cluster_ID}, Descrption: {desc}"
        cluster_descriptions.append(formatted_txt)
    return ("\n").join(cluster_descriptions)