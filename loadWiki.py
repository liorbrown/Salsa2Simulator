import requests
from bs4 import BeautifulSoup
limit = 100
def get_urls_recursively(url):
    global limit
    # Stop if the limit is reached
    if limit:
        try:
            # Request the page content
            response = requests.get(url)
            response.raise_for_status()  # Ensure successful response
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all anchor tags
            links = soup.find_all('a', href=True)
            
            # Print the URLs from the anchor tags
            for link in links:
                if limit == 0:
                    return
                
                href = link['href']

                if href != url:
                    print(href)
                    limit -= 1
                    # Only recurse if the link is a valid Wikipedia URL (optional check)
                    if href.startswith('http'):
                        get_urls_recursively(href)
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

# Example usage: start with the Wikipedia main page and set a limit of 3 recursions
get_urls_recursively("https://en.wikipedia.org/wiki/Main_Page")