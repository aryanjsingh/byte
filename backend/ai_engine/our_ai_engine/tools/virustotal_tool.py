import os
import vt
import json
from langchain_core.tools import tool

@tool
def virustotal_scan(target: str) -> str:
    """
    Scans a URL or File Hash (MD5, SHA-1, SHA-256) using VirusTotal API.
    Provide a URL to scan or a file hash to retrieve a report.
    """
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        return "Error: VIRUSTOTAL_API_KEY environment variable not set."

    try:
        client = vt.Client(api_key)
        
        # Check if target is likely a URL (contains http or is domain-like) or Hash
        if "http" in target or "." in target and len(target) < 64: # Simple heuristic for URL
             # URL Scan
             # First, scan the URL
            analysis = client.scan_url(target)
            # Wait for completion? No, usually we just get the id and check, but for a chatbot simple tool 
            # let's try to get an existing report or just info. 
            # Actually, getting an object is better.
            
            # Let's verify if we can just get the url identifier
            url_id = vt.url_id(target)
            try:
                obj = client.get_object("/urls/{}", url_id)
                stats = obj.last_analysis_stats
                
                result = f"VirusTotal URL Report for {target}:\n"
                result += f"Malicious: {stats.get('malicious', 0)}\n"
                result += f"Suspicious: {stats.get('suspicious', 0)}\n"
                result += f"Harmless: {stats.get('harmless', 0)}\n"
                result += f"Link: https://www.virustotal.com/gui/url/{url_id}"
                
                client.close()
                return result
            except vt.error.APIError:
                 # If not found, maybe new submission?
                 client.close()
                 return f"URL {target} submitted for scanning. Please check VirusTotal later (synchronous wait not implemented for speed)."

        else:
            # File Hash
            try:
                obj = client.get_object("/files/{}", target)
                stats = obj.last_analysis_stats
                
                result = f"VirusTotal File Report for {target}:\n"
                result += f"Malicious: {stats.get('malicious', 0)}\n"
                result += f"Suspicious: {stats.get('suspicious', 0)}\n"
                result += f"Harmless: {stats.get('harmless', 0)}\n"
                result += f"Link: https://www.virustotal.com/gui/file/{target}"
                
                client.close()
                return result
            except vt.error.APIError as e:
                client.close()
                return f"Error retrieving file report: {str(e)}"

    except Exception as e:
        return f"An unexpected error occurred with VirusTotal: {str(e)}"
