from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import httpx
from typing import Dict, Any, Optional, List
from serpapi import SerpApiClient as SerpApiSearch

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("SERPAPI_API_KEY")

# Ensure API key is present
if not API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in environment variables. Please set it in the .env file.")

# Initialize the MCP server
mcp = FastMCP("SerpApi MCP Server")

# Tool to perform web searches via SerpApi
@mcp.tool()
async def search(params: Dict[str, Any] = {}) -> str:
    """Perform a web search using SerpApi.

    Args:
        params: Dictionary of engine-specific parameters (e.g., {"q": "Coffee", "engine": "google_light", "location": "Austin, TX"}).

    Returns:
        A formatted string of search results or an error message.
    """

    params = {
        "api_key": API_KEY,
        "engine": "google_light", # Fastest engine by default
        **params  # Include any additional parameters
    }

    try:
        search = SerpApiSearch(params)
        data = search.get_dict()

        # Process organic search results if available
        if "organic_results" in data:
            formatted_results = []
            for result in data.get("organic_results", []):
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "No snippet")
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
            return "\n".join(formatted_results) if formatted_results else "No organic results found"
        else:
            return "No organic results found"

    # Handle HTTP-specific errors
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        elif e.response.status_code == 401:
            return "Error: Invalid API key. Please check your SERPAPI_API_KEY."
        else:
            return f"Error: {e.response.status_code} - {e.response.text}"
    # Handle other exceptions (e.g., network issues)
    except Exception as e:
        return f"Error: {str(e)}"

# Tool to perform image searches via SerpApi
@mcp.tool()
async def image_search(
    query: str,
    count: Optional[int] = 5,
    start: Optional[int] = 1,
    params: Optional[Dict[str, Any]] = None
) -> str:
    """Search for images using SerpApi's Google Images engine.

    Args:
        query: The search query for images
        count: Number of image results to return (1-10, default 5)
        start: Pagination start index (default 1)
        params: Optional additional parameters for the search

    Returns:
        A formatted string of image search results or an error message.
    """
    if count > 10:
        count = 10  # Limit to 10 results max
    
    search_params = {
        "api_key": API_KEY,
        "engine": "google_images",
        "q": query,
        "ijn": (start - 1) // 10,  # Page number for pagination
        "num": count
    }
    
    # Add any additional parameters
    if params:
        search_params.update(params)
    
    try:
        search = SerpApiSearch(search_params)
        data = search.get_dict()
        
        # Handle if no results
        if "error" in data:
            return f"Error: {data['error']}"
        
        # Process image results
        image_results = data.get("images_results", [])
        if not image_results:
            return "No image results found for your query."
            
        formatted_results: List[str] = []
        for i, image in enumerate(image_results[:count]):
            title = image.get("title", "No title")
            original_image = image.get("original", "")
            thumbnail = image.get("thumbnail", "")
            source = image.get("source", "Unknown")
            
            formatted_results.append(
                f"[{i+1}] Title: {title}\n"
                f"Source: {source}\n"
                f"Image URL: {original_image}\n"
                f"Thumbnail: {thumbnail}\n"
            )
            
        # Add related searches if available
        if "related_searches" in data and data["related_searches"]:
            related_queries = [item.get("query", "") for item in data["related_searches"][:5]]
            formatted_results.append("\nRelated Searches: " + ", ".join(related_queries))
            
        return "\n\n".join(formatted_results)
    
    # Handle exceptions
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        elif e.response.status_code == 401:
            return "Error: Invalid API key. Please check your SERPAPI_API_KEY."
        else:
            return f"Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# Run the server
if __name__ == "__main__":
    mcp.run()