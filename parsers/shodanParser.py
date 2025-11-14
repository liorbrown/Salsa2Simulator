import shodan
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #disable warnings.

API_KEY = "mPbkgYLMsJC8gZ62CDeaNK6yPArPkgEN"
shodan_client = shodan.Shodan(API_KEY)
shodan_client._session.verify = False  # Disable SSL verification

# Example: Search for HTTP-only websites
results = shodan_client.search('port:80 -ssl')

i = 50
for site in results['matches']:
    i -= 1
    if not i:
        sys.exit()
    print(site['ip_str'])