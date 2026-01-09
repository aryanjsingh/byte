"""
Image Search Tool using Google Custom Search API
Fetches relevant images for definitional queries
"""
import os
import requests
from typing import List, Dict
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()


def search_images(query: str, num_results: int = 4) -> List[Dict[str, str]]:
    """
    Search for images using Google Custom Search API
    
    Args:
        query: Search term
        num_results: Number of images to return (max 10)
    
    Returns:
        List of dicts with 'url', 'thumbnail', 'title'
    """
    api_key = os.getenv("GOOGLE_IMAGE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    
    if not api_key:
        print("❌ No API key found")
        return []
    
    if not cx:
        print("⚠️ No CX ID found, using default Google image search")
        # For image search without custom engine, we need a different approach
        # Use a generic web search CX or create error message
        print("❌ GOOGLE_CUSTOM_SEARCH_ENGINE_ID not set in .env")
        return []
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "searchType": "image",
            "num": min(num_results, 10),
            "safe": "active",  # Safe search
            "imgSize": "xlarge"  # High quality images
        }
        
        print(f"🔍 Searching for images: {query}")
        response = requests.get(url, params=params, timeout=5)
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.text[:200]}")
            return []
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"✅ Found {len(items)} images")
        
        images = []
        for item in items[:num_results]:
            images.append({
                "url": item.get("link", ""),
                "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
                "title": item.get("title", "")
            })
        
        return images
    
    except Exception as e:
        print(f"❌ Image search error: {e}")
        return []


@tool
def image_search(query: str) -> str:
    """
    Search for images related to any term or concept.
    Use this tool when users ask definitional questions like:
    - "What is phishing?"
    - "What is iOS?"
    - "Explain ransomware"
    - "Define social engineering"
    - "What is machine learning?"
    - "What is an iPhone?"
    
    Returns a formatted string with image URLs that can be displayed to the user.
    """
    print(f"🔧 TOOL CALLED: image_search")
    print(f"📝 Query: {query}")
    
    # Search directly without adding extra context to keep it general
    images = search_images(query, num_results=4)
    
    if not images:
        return "No images found for this query."
    
    # Format as JSON-like string for easy parsing
    result = f"Found {len(images)} images:\n"
    for i, img in enumerate(images, 1):
        result += f"{i}. {img['title'][:50]}\n"
        result += f"   URL: {img['url']}\n"
        result += f"   Thumbnail: {img['thumbnail']}\n"
    
    print(f"✅ TOOL RESULT: {len(images)} images found")
    
    # Return structured data as JSON string for frontend parsing
    import json
    return json.dumps({
        "type": "image_results",
        "images": images,
        "query": query
    })
