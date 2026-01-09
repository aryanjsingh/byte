import os
import json
import requests
from langchain_core.tools import tool

def _whoisxml_lookup_with_requests(domain: str, api_key: str) -> str:
    """
    WhoisXML API domain lookup using requests library.
    Retrieves WHOIS information for a domain.
    """
    print(f"🔍 WHOIS LOOKUP: Starting lookup for domain: {domain}")
    
    # Clean domain - remove protocol if present
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"🔍 WHOIS LOOKUP: Cleaned domain: {domain}")
    
    api_url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    
    params = {
        "apiKey": api_key,
        "domainName": domain,
        "outputFormat": "JSON"
    }
    
    try:
        print(f"🔍 WHOIS LOOKUP: Requesting {api_url}")
        response = requests.get(api_url, params=params, timeout=30)
        print(f"🔍 WHOIS LOOKUP: Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key information
            whois_record = data.get("WhoisRecord", {})
            registrar = whois_record.get("registrarName", "N/A")
            created_date = whois_record.get("createdDate", "N/A")
            expires_date = whois_record.get("expiresDate", "N/A")
            updated_date = whois_record.get("updatedDate", "N/A")
            
            # Registrant info
            registrant = whois_record.get("registrant", {})
            registrant_name = registrant.get("name", "N/A")
            registrant_org = registrant.get("organization", "N/A")
            registrant_country = registrant.get("country", "N/A")
            
            # Name servers
            name_servers = whois_record.get("nameServers", {})
            if isinstance(name_servers, dict):
                ns_list = name_servers.get("hostNames", [])
            else:
                ns_list = name_servers if isinstance(name_servers, list) else []
            
            ns_text = ", ".join(ns_list[:3]) if ns_list else "N/A"
            
            result = f"WhoisXML Domain Report for {domain}:\n"
            result += f"Registrar: {registrar}\n"
            result += f"Created Date: {created_date}\n"
            result += f"Expires Date: {expires_date}\n"
            result += f"Updated Date: {updated_date}\n"
            result += f"Registrant: {registrant_name}\n"
            result += f"Organization: {registrant_org}\n"
            result += f"Country: {registrant_country}\n"
            result += f"Name Servers: {ns_text}\n"
            
            print(f"✅ WHOIS LOOKUP: Success - {result[:100]}...")
            return result
            
        elif response.status_code == 422:
            return f"Domain {domain} appears to be invalid or not registered."
        else:
            print(f"❌ WHOIS LOOKUP: Error response: {response.text[:200]}")
            return f"WhoisXML API error: {response.status_code} - {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        print(f"❌ WHOIS LOOKUP: Request timed out")
        return "WhoisXML request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"❌ WHOIS LOOKUP: Request error: {e}")
        return f"WhoisXML request failed: {str(e)}"
    except Exception as e:
        print(f"❌ WHOIS LOOKUP: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return f"An unexpected error occurred with WhoisXML: {str(e)}"


@tool
def whoisxml_lookup(domain: str) -> str:
    """
    Looks up WHOIS information for a domain using WhoisXML API.
    Provides registrar, creation date, expiration date, and registrant information.
    """
    print(f"🔧 TOOL CALLED: whoisxml_lookup with domain={domain}")
    
    api_key = os.getenv("WHOISXML_API_KEY")
    if not api_key:
        print("❌ TOOL ERROR: No API key found")
        return "Error: WHOISXML_API_KEY environment variable not set."
    
    print(f"✅ TOOL: API key found (length: {len(api_key)})")
    result = _whoisxml_lookup_with_requests(domain, api_key)
    print(f"✅ TOOL RESULT: {result[:100]}...")
    return result
