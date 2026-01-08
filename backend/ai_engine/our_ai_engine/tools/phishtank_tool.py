import os
import requests
import base64
from langchain_core.tools import tool

@tool
def phishtank_url_check(url: str) -> str:
    """
    Checks if a URL is a known phishing site using PhishTank database.
    Note: PhishTank API often is just a data dump or requires a key for better rate limits.
    We will try to use the check-url endpoint.
    """
    api_key = os.getenv("PHISHTANK_API_KEY")
    # PhishTank key is optional but recommended
    
    endpoint = "https://checkurl.phishtank.com/checkurl/"
    payload = {
        'url': url,
        'format': 'json'
    }
    if api_key:
        payload['app_key'] = api_key

    try:
        # PhishTank POST request to check url
        response = requests.post(endpoint, data=payload)
        
        # Handling the weirdness of PhishTank API responses (sometimes XML even if JSON requested if error)
        # But let's assume JSON as requested.
        try:
            data = response.json()
        except Exception:
            # Fallback if not json
            return f"PhishTank API returned non-JSON response: {response.text[:200]}..."

        if 'results' in data and 'in_database' in data['results']:
            in_db = data['results']['in_database']
            result_str = f"PhishTank Report for {url}:\n"
            result_str += f"In Database: {in_db}\n"
            
            if in_db:
                valid = data['results'].get('valid_phish', False)
                result_str += f"Valid Phish: {valid}\n"
                result_str += f"Link: {data['results'].get('phish_detail_page')}"
            else:
                result_str += "Status: Not found in PhishTank database (Likely Safe)"
            
            return result_str
        else:
            return f"Unexpected response structure from PhishTank: {data.keys()}"

    except Exception as e:
        return f"An unexpected error occurred with PhishTank: {str(e)}"
