from tools import virustotal_scan, shodan_device_search, greynoise_ip_check, phishtank_url_check
import os
from dotenv import load_dotenv

load_dotenv()

def test_tools():
    print("Testing Security Tools...")
    
    # We expect these to fail gracefully if keys aren't present.
    
    print("\n--- VirusTotal ---")
    res_vt = virustotal_scan.invoke("example.com")
    print(res_vt)

    print("\n--- Shodan ---")
    res_shodan = shodan_device_search.invoke("apache")
    print(res_shodan)
    
    print("\n--- GreyNoise ---")
    res_gn = greynoise_ip_check.invoke("8.8.8.8")
    print(res_gn)
    
    print("\n--- PhishTank ---")
    res_pt = phishtank_url_check.invoke("http://google.com")
    print(res_pt)

if __name__ == "__main__":
    test_tools()
