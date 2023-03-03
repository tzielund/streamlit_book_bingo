import datetime
import json
import os
import subprocess
import time

import streamlit
import requests
from requests.structures import CaseInsensitiveDict
import dateutil.parser

# import logging
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1
#
# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

streamlit.title("Spotify playlist test")

streamlit.header("Authentication")
streamlit.write("Paste in your spotify API token from a current browser session.")
bearer = ""
if "spotify_bearer" in streamlit.session_state:
    bearer = streamlit.session_state["spotify_bearer"]
token = streamlit.text_input("Paste in bearer token", value=bearer)
if not token:
    streamlit.stop()
streamlit.session_state["spotify_bearer"] = token

headers = CaseInsensitiveDict()
headers = CaseInsensitiveDict()
headers["Authorization"] = token
headers["Content-Type"] = "application/json"

# Spotify utils

CACHE_DIR = "spotify_cache/"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_playlist_list(headers):
    cache_filename = f"{CACHE_DIR}playlist_list.json"
    result = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    if result.status_code != 200:
        streamlit.write(result.status_code)
        streamlit.write(result.text)
        streamlit.stop()
    items = result.json()["items"]
    with open (cache_filename, 'w') as OUT:
        OUT.write(json.dumps(items, indent=4))
    return items

def safe_remove(track_struct, field_list):
    if len(field_list) == 0:
        return
    if not isinstance(track_struct, dict):
        return
    lookfor = field_list[0]
    if lookfor not in track_struct:
        return
    if len(field_list) == 1:
        if track_struct[lookfor] is None:
            track_struct[lookfor] = 'x'
        del (track_struct[lookfor])
    else:
        tail = field_list[1:]
        new_context = field_list[lookfor]
        safe_remove(new_context, tail)

REMOVE_LIST = [
    "added_at", "added_by", "is_local", "primary_color", "sharing_info",
    "track/album", "track/available_markets"
]
def simplify(track_struct):
    for item in REMOVE_LIST:
        splits = item.split("/")
        print (f"removing {item}")
        safe_remove(track_struct, splits)


def cache_playlist(headers, playlist_id, playlist_metadata):
    new_snapshot = playlist_metadata["snapshot_id"]
    playlist_file = CACHE_DIR + playlist_id + ".json"
    if os.path.exists(playlist_file):
        with open (playlist_file) as IN:
            playlist_details = json.load(IN)
            cached_snapshot = playlist_details["snapshot_id"]
            if cached_snapshot == new_snapshot:
                print(f"Cached {playlist_id} is still valid")
                for item in playlist_details:
                    # Simplify each item by deleting some useless stuff
                    simplify(item)
        with open (playlist_file, 'w') as OUT:
            OUT.write(json.dumps(playlist_details,indent=4))
        return playlist_details
    # If here, we must extract the full playlist and cache it
    streamlit.write(f"Caching playlist {playlist_metadata['name']}")
    prog = streamlit.progress(0.0)
    total = playlist_metadata['tracks']['total']+1
    playlist_tracks = list()
    done = False
    offset = 0
    pagesize = 50
    print(f"Preparing to extract {playlist_id}")
    while not done:
        print (f"Offset {offset}")
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        url += f"?offset={offset}&limit=50"
        print (url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            response.status_code
            response.text
            return
        jsondata = response.json()
        # streamlit.json(jsondata)
        itemlist = jsondata["items"]
        for item in itemlist:
            # Simplify each item by deleting some useless stuff
            simplify(item)
        prog.progress(len(playlist_tracks)/total)
        print (f"Found {len(itemlist)}")
        playlist_tracks.extend(itemlist)
        if len(itemlist) < pagesize:
            done = True
        offset += pagesize
        time.sleep(2)
        # done = True
    playlist_metadata["items"] = playlist_tracks
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(playlist_metadata, indent=4))
    return playlist_tracks

def get_recently_played(headers):
    recent_list = list()
    done = False
    oldest = None
    while not done:
        recent_url = f"https://api.spotify.com/v1/me/player/recently-played"
        params = {}
        if oldest:
            params["before"] = oldest
            print (f"Again, before {oldest}")
        recent_result = requests.get(recent_url, headers=headers, params=params)
        recent_result.status_code
        if recent_result.status_code != 200:
            recent_result.text
        recent_json = recent_result.json()
        recent_items = recent_json["items"]
        if len(recent_list) > 200 or len(recent_items) == 0:
            done = True
        for item in recent_items:
            # streamlit.json(item)
            track = item["track"]
            if 'id' not in track:
                print ("What the...")
                print (json.dumps(item, indent=2))
                continue
            recent_list_struct = dict()
            recent_list_struct["id"] = track["id"]
            recent_list_struct["name"] = track["name"]
            pAt = item["played_at"]
            pAtDt = dateutil.parser.isoparse(pAt)
            pAtTs = int(round(pAtDt.timestamp()))
            oldest = pAtTs
            recent_list_struct["played_at"] = pAt
            recent_list_struct["played_at_timestamp"] = pAtTs
            recent_list.append(recent_list_struct)
    return recent_list

playlist_list = get_cached_playlist_list(headers)

master_playlist_name = "master playlist"
master_unrecent_name = "not recently played"

for playlist in playlist_list:
    if playlist["name"] == master_playlist_name:
        master_playlist = playlist
    if playlist["name"] == master_unrecent_name:
        master_unrecent = playlist

# master_unrecent
streamlit.header("Not recently played copy")
streamlit.write(f"Name: {master_unrecent['name']}")
unrecent_id = master_unrecent['id']
streamlit.write(f"Id: {unrecent_id}")
streamlit.write(f"Size: {master_unrecent['tracks']['total']}")
streamlit.write(f"SnapshotID: {master_unrecent['snapshot_id']}")
cache_playlist(headers, unrecent_id, master_unrecent)

# master_playlist
master_id = master_playlist['id']
master_snapshot = master_playlist['snapshot_id']
streamlit.header("Master playlist")
streamlit.write(f"Name: {master_playlist['name']}")
streamlit.write(f"Id: {master_id}")
streamlit.write(f"Size: {master_playlist['tracks']['total']}")
streamlit.write(f"SnapshotID: {master_snapshot}")
cache_playlist(headers, master_id, master_playlist)

# Recently Played
recent_list = get_recently_played(headers)

streamlit.json(recent_list)