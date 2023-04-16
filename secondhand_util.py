from html.parser import HTMLParser

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
CACHE_ARTIST_MATCH_FILE = f"{CACHE_BASE_SH}/artist_match.json"

HEADER = {"Accept": "application/json"}
BASE_URL = ""
SEARCH_URL = "https://secondhandsongs.com/search?search_text={url_safe_name}&format=json"

def store_secondhand_streamlit_artist_mapping(mapping):
    with open (CACHE_ARTIST_MATCH_FILE, 'w') as OUT:
        OUT.write(json.dumps(mapping, indent=4))

def cache_secondhand_streamlit_artist_mapping():
    try:
        with open (CACHE_ARTIST_MATCH_FILE) as IN:
            result = json.load(IN)
            return result
    except:
        result = {}
        store_secondhand_streamlit_artist_mapping(result)
        return result


def link_simple_search(name):
    """Searches for a name, presumably an artist or work."""
    url_safe_name = urllib.parse.quote(name)
    url = SEARCH_URL.format(url_safe_name=url_safe_name)
    return url


def cache_simple_search(name):
    """Searches for a name, presumably an artist or work."""
    url_safe_name = urllib.parse.quote(name.replace("/","_"))
    filename = f"{CACHE_SEARCH_SH}{url_safe_name}.json"
    if os.path.exists(filename):
        with open (filename) as IN:
            data = IN.read()
            return data
    url = SEARCH_URL.format(url_safe_name=url_safe_name)
    print (url)
    response = requests.get(url, headers=HEADER)
    if response.status_code == 200:
        print(response.text)
        result_html = response.text
        with open (filename, 'w') as OUT:
            OUT.write(result_html)
        return result_html
    else:
        print(f"REST error {response.status_code}: {response.text}")
        return ""


class SecondhandArtistSearchHtmlParser(HTMLParser):

    currentlyInATag = False
    currentHref = ""
    currentData = ""
    hrefs = dict()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attrpair in attrs:
                if attrpair[0] == "href":
                    target = attrpair[1]
                    if target.startswith("/artist/"):
                        self.currentHref = attrpair[1]
                        self.currentData = ""
                        self.currentlyInATag = True

    def handle_endtag(self, tag):
        if self.currentlyInATag and tag == "a":
            self.hrefs[self.currentHref] = self.currentData
            self.currentlyInATag = False

    def handle_data(self, data):
        if self.currentlyInATag:
            self.currentData += data

    def get_search_results(self):
        return self.hrefs

    def reset_search(self):
        self.currentlyInATag = False
        self.currentHref = ""
        self.currentData = ""
        self.hrefs = dict()