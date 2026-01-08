import os
from greynoise import GreyNoise
from greynoise.api import APIConfig
from langchain_core.tools import tool

@tool
def greynoise_ip_check(ip_address: str) -> str:
    """
    Checks the reputation of an IP address using GreyNoise Community API.
    Provides classification, actor, and noise/riot status.
    This tool works even without a GREYNOISE_API_KEY.
    """
    api_key = os.getenv("GREYNOISE_API_KEY", "")

    try:
        # Initialize GreyNoise client with Community offering
        # This allows lookups even without an API key (within rate limits)
        config = APIConfig(api_key=api_key, offering="community")
        session = GreyNoise(config=config)
        
        # When offering is 'community', session.ip() calls the community endpoint
        data = session.ip(ip_address)
        
        # Parse fields from community response
        noise = data.get('noise', False)
        riot = data.get('riot', False)
        classification = data.get('classification', 'unknown')
        name = data.get('name', 'Unknown Service')
        last_seen = data.get('last_seen', 'Never')

        result = f"GreyNoise Community Report for {ip_address}:\n"
        result += f"- Noise: {noise}\n"
        result += f"- RIOT: {riot}\n"
        result += f"- Classification: {classification}\n"
        result += f"- Service/Name: {name}\n"
        result += f"- Last Seen: {last_seen}\n"
        result += f"- Link: {data.get('link', f'https://viz.greynoise.io/ip/{ip_address}')}"
        
        return result

    except Exception as e:
        return f"An unexpected error occurred with GreyNoise Community API: {str(e)}"
