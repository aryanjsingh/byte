import os
import json
import requests
import base64
import hashlib
from langchain_core.tools import tool

def _vt_scan_with_requests(target: str, api_key: str) -> str:
    """
    VirusTotal scan using requests library (no async issues).
    Works in any context without event loop conflicts.
    """
    print(f"🔍 VT SCAN: Starting scan for target: {target}")
    
    headers = {
        "x-apikey": api_key,
        "Accept": "application/json"
    }
    
    try:
        # Check if target is likely a URL or Hash
        is_url = "http" in target.lower() or ("." in target and len(target) < 64 and not target.isalnum())
        
        if is_url:
            print(f"🔍 VT SCAN: Detected URL, encoding...")
            # URL scan - need to base64 encode the URL
            url_id = base64.urlsafe_b64encode(target.encode()).decode().strip("=")
            api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            print(f"🔍 VT SCAN: Requesting {api_url}")
            
            response = requests.get(api_url, headers=headers, timeout=30)
            print(f"🔍 VT SCAN: Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                
                result = f"VirusTotal URL Report for {target}:\n"
                result += f"Malicious: {stats.get('malicious', 0)}\n"
                result += f"Suspicious: {stats.get('suspicious', 0)}\n"
                result += f"Harmless: {stats.get('harmless', 0)}\n"
                result += f"Undetected: {stats.get('undetected', 0)}\n"
                result += f"Link: https://www.virustotal.com/gui/url/{url_id}"
                
                print(f"✅ VT SCAN: Success - {result[:100]}...")
                return result
            elif response.status_code == 404:
                # URL not found, submit for scanning
                print(f"🔍 VT SCAN: URL not in database, submitting for scan...")
                submit_url = "https://www.virustotal.com/api/v3/urls"
                submit_response = requests.post(
                    submit_url, 
                    headers=headers, 
                    data={"url": target},
                    timeout=30
                )
                if submit_response.status_code in [200, 201]:
                    return f"URL {target} has been submitted to VirusTotal for scanning. Results will be available shortly at: https://www.virustotal.com/gui/url/{url_id}"
                else:
                    return f"Could not submit URL for scanning. Status: {submit_response.status_code}"
            else:
                print(f"❌ VT SCAN: Error response: {response.text[:200]}")
                return f"VirusTotal API error: {response.status_code} - {response.text[:100]}"
        else:
            # File hash scan
            print(f"🔍 VT SCAN: Detected file hash...")
            api_url = f"https://www.virustotal.com/api/v3/files/{target}"
            print(f"🔍 VT SCAN: Requesting {api_url}")
            
            response = requests.get(api_url, headers=headers, timeout=30)
            print(f"🔍 VT SCAN: Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                
                result = f"VirusTotal File Report for {target}:\n"
                result += f"Malicious: {stats.get('malicious', 0)}\n"
                result += f"Suspicious: {stats.get('suspicious', 0)}\n"
                result += f"Harmless: {stats.get('harmless', 0)}\n"
                result += f"Undetected: {stats.get('undetected', 0)}\n"
                result += f"Link: https://www.virustotal.com/gui/file/{target}"
                
                print(f"✅ VT SCAN: Success - {result[:100]}...")
                return result
            elif response.status_code == 404:
                return f"File hash {target} not found in VirusTotal database."
            else:
                print(f"❌ VT SCAN: Error response: {response.text[:200]}")
                return f"VirusTotal API error: {response.status_code}"
                
    except requests.exceptions.Timeout:
        print(f"❌ VT SCAN: Request timed out")
        return "VirusTotal request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"❌ VT SCAN: Request error: {e}")
        return f"VirusTotal request failed: {str(e)}"
    except Exception as e:
        print(f"❌ VT SCAN: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return f"An unexpected error occurred with VirusTotal: {str(e)}"


@tool
def virustotal_scan(target: str) -> str:
    """
    Scans a URL or File Hash (MD5, SHA-1, SHA-256) using VirusTotal API.
    Provide a URL to scan or a file hash to retrieve a report.
    """
    print(f"🔧 TOOL CALLED: virustotal_scan with target={target}")
    
    # Fix common URL mangling issues from LLMs
    original_target = target
    
    # Fix "https-" or "http-" to "https://" or "http://"
    if target.startswith("https-") and "://" not in target:
        target = "https://" + target[6:]
        print(f"🔧 TOOL: Fixed URL from '{original_target}' to '{target}'")
    elif target.startswith("http-") and "://" not in target:
        target = "http://" + target[5:]
        print(f"🔧 TOOL: Fixed URL from '{original_target}' to '{target}'")
    # Handle case where :// is missing entirely
    elif ("." in target and "/" in target) and "://" not in target and not target.startswith("http"):
        # Looks like a URL without protocol
        target = "https://" + target
        print(f"🔧 TOOL: Added https:// to '{original_target}' -> '{target}'")
    
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        print("❌ TOOL ERROR: No API key found")
        return "Error: VIRUSTOTAL_API_KEY environment variable not set."
    
    print(f"✅ TOOL: API key found (length: {len(api_key)})")
    result = _vt_scan_with_requests(target, api_key)
    print(f"✅ TOOL RESULT: {result[:100]}...")
    return result
