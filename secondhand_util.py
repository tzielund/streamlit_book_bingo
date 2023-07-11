from html.parser import HTMLParser

import requests
import urllib
import os
import json

CACHE_BASE_SH = "secondhand_cache/"
os.makedirs(CACHE_BASE_SH, exist_ok=True)
CACHE_SEARCH_SH = f"{CACHE_BASE_SH}search/"
os.makedirs(CACHE_SEARCH_SH, exist_ok=True)
CACHE_ARTIST_COVERS_SH = f"{CACHE_BASE_SH}artists/covers/"
os.makedirs(CACHE_ARTIST_COVERS_SH, exist_ok=True)
CACHE_ARTIST_ORIGS_SH = f"{CACHE_BASE_SH}artists/originals/"
os.makedirs(CACHE_ARTIST_ORIGS_SH, exist_ok=True)
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
        elif tag == 'div':
            # print("Found a DIV tag")
            isRootWrapper = False
            dataController = ""
            for attrpair in attrs:
                if attrpair[1] == "root_wrapper" and attrpair[0] == "id":
                    isRootWrapper = True
                elif attrpair[0] == "data-controller":
                    dataController = attrpair[1]
            if isRootWrapper and dataController:
                self.hrefs[self.currentHref] = dataController
        else:
            pass
            # print(f"Tag: {tag}")

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


def cache_simple_search(name):
    """Searches for a name, presumably an artist or work."""
    url_safe_name = urllib.parse.quote(name.replace("/","_"))
    filename = f"{CACHE_SEARCH_SH}{url_safe_name}.json"
    if os.path.exists(filename):
        with open (filename) as IN:
            data = json.load(IN)
            return data
    url = SEARCH_URL.format(url_safe_name=url_safe_name)
    print (url)
    response = requests.get(url, headers=HEADER)
    if response.status_code == 200:
        result_html = response.text
        try:
            result_json = json.loads(result_html)
            print(json.dumps(result_json, indent=4))
            if "uri" in result_json:
                # Good news, we hit a single exact result.  Return it as a single key dictionary
                uri = result_json["uri"]
                commonName = result_json["commonName"]
                if uri.startswith("https://secondhandsongs.com/artist/"):
                    short_uri = uri[27:]
                    result = {short_uri: commonName}
                else:
                    print("URI doesn't match")
        except ValueError:
            artist_search_parser = SecondhandArtistSearchHtmlParser()
            artist_search_parser.reset_search()
            artist_search_parser.feed(result_html)
            hrefs = artist_search_parser.get_search_results()
            result = hrefs

        with open (filename, 'w') as OUT:
            OUT.write(json.dumps(result, indent=4))
        return result
    else:
        print(f"REST error {response.status_code}: {response.text}")
        return {}

def cache_covers_list(artist_id_with_artist_prefix):
    # Assume the parameter is like "/artist/1393"
    if artist_id_with_artist_prefix.startswith("/artist/"):
        id_only = artist_id_with_artist_prefix[8:]
    else:
        raise RuntimeError(f"Supplied artist must start with /artist/ (given {artist_id_with_artist_prefix})")
    filename = f"{CACHE_ARTIST_COVERS_SH}{id_only}.json"
    if os.path.exists(filename):
        with open (filename) as IN:
            result = json.load(IN)
            return result
    url = f"https://secondhandsongs.com{artist_id_with_artist_prefix}/performances?format=json"
    result = requests.get(url)
    if result.status_code != 200:
        print(f"Error: {result.status_code}, {result.text}")
        return {}
    rjson = result.json()
    with open (filename, 'w') as OUT:
        OUT.write(json.dumps(rjson, indent=4))
    return rjson

