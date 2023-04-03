import requests
import urllib
import os
import json

CACHE_BASE_SH = "secondhand_cache/"
os.makedirs(CACHE_BASE_SH, exist_ok=True)
CACHE_SEARCH_SH = f"{CACHE_BASE_SH}search/"
os.makedirs(CACHE_SEARCH_SH, exist_ok=True)
CACHE_ARTIST_COVERS_SH = f"{CACHE_BASE_SH}artists/"
os.makedirs(CACHE_ARTIST_COVERS_SH, exist_ok=True)
CACHE_ARTIST_SH = f"{CACHE_BASE_SH}artists/"
os.makedirs(CACHE_ARTIST_SH, exist_ok=True)

HEADER = {"Accept": "application/json"}
BASE_URL = ""
SEARCH_URL = "https://secondhandsongs.com/search?search_text={url_safe_name}&format=json"

def link_simple_search(name):
    """Searches for a name, presumably an artist or work."""
    url_safe_name = urllib.parse.quote(name)
    url = SEARCH_URL.format(url_safe_name=url_safe_name)
    return url


def cache_simple_search(name):
    """Searches for a name, presumably an artist or work."""
    url_safe_name = urllib.parse.quote(name)
    filename = f"{CACHE_SEARCH_SH}{url_safe_name}.json"
    if os.path.exists(filename):
        with open (filename) as IN:
            data = json.loads(IN)
            return data
    url = SEARCH_URL.format(url_safe_name=url_safe_name)
    print (url)
    response = requests.get(url, headers=HEADER)
    if response.status_code == 200:
        print(response.text)
        result_html = response.text
        return result_html
    else:
        raise RuntimeError(f"REST error {response.status_code}: {response.text}")
