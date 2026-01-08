import os
import shodan
from langchain_core.tools import tool

@tool
def shodan_device_search(query: str) -> str:
    """
    Searches Shodan for devices using a query string (e.g., "apache", "port:22").
    Returns a summary of the top matches.
    """
    api_key = os.getenv("SHODAN_API_KEY")
    if not api_key:
        return "Error: SHODAN_API_KEY environment variable not set."

    try:
        api = shodan.Shodan(api_key)
        results = api.search(query, limit=5)

        summary = f"Shodan Search Results for '{query}' (Total: {results['total']}):\n"
        for result in results['matches']:
            ip = result.get('ip_str')
            port = result.get('port')
            org = result.get('org', 'Unknown API')
            location = result.get('location', {}).get('country_name', 'Unknown')
            summary += f"- {ip}:{port} | Org: {org} | Loc: {location}\n"
        
        return summary

    except shodan.APIError as e:
        return f"Shodan API Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred with Shodan: {str(e)}"
