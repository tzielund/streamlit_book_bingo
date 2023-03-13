import os

import streamlit
from requests.structures import CaseInsensitiveDict

from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

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
headers["Authorization"] = token
headers["Content-Type"] = "application/json"

def summarize_playlist(playlist_metadata, playlist_tracks):
    plid = playlist_metadata['id']
    streamlit.header(playlist_metadata.get("name",plid))
    streamlit.write(f"Total: {playlist_metadata['tracks']['total']}")
    # for trackid in playlist_tracks.keys():
    #     item = playlist_tracks[trackid]
    #     streamlit.markdown(f"* {item['name']}")

def list_playlist(playlist_metadata, playlist_tracks):
    plid = playlist_metadata['id']
    streamlit.sidebar.header(playlist_metadata.get("name",plid))
    default_artists = [{'name':'no name'}]
    for trackid in playlist_tracks.keys():
        item = playlist_tracks[trackid]
        label = f"{item['name']} by {item.get('artists',default_artists)[0]['name']}"
        url = f"https://open.spotify.com/track/{trackid}"
        streamlit.sidebar.markdown(f"* [{label}]({url})")


playlist_list = get_cached_playlist_list(headers)

master_playlist_name = "master playlist"
unrecent_playlist_name = "not recently played"
recent_playlist_name = "Recently Played"

for playlist in playlist_list:
    if playlist["name"] == master_playlist_name:
        master_playlist = playlist
    if playlist["name"] == unrecent_playlist_name:
        unrecent_playlist = playlist
    if playlist["name"] == recent_playlist_name:
        recent_playlist = playlist

master_id = master_playlist['id']
master_list = cache_playlist(headers, master_id, master_playlist)


recent_id = recent_playlist['id']
recent_list = cache_playlist(headers, recent_id, recent_playlist)
# recent_list

unrecent_id = unrecent_playlist['id']
unrecent_list = cache_playlist(headers, unrecent_id, unrecent_playlist)

# Recently Played
refresh_rp = streamlit.sidebar.button("Refresh recently played")
recent_plays = get_recently_played(headers, ignore_cache=refresh_rp)
summarize_playlist({'id':"$RECENT", 'tracks':{'total':len(recent_plays)}}, recent_plays)

streamlit.header("What needs to be done")

to_be_added_to_rp = dict()
for rpid in recent_plays:
    if rpid not in (recent_list):
        to_be_added_to_rp[rpid] = recent_plays[rpid]
if to_be_added_to_rp:
    streamlit.write("Recently played tracks not found in the Recently Played playlist:")
    for id in to_be_added_to_rp.keys():
        label = f"{recent_plays[id]['name']}"
        url = f"https://open.spotify.com/track/{id}"
        streamlit.markdown(f"[{label}]({url})")
    sync_to_be_added_to_rp = streamlit.button("Sync these to Recently Played")
    if sync_to_be_added_to_rp:
        streamlit.write("Attempting to add items to playlist")
        add_to_playlist(headers, recent_playlist, list(to_be_added_to_rp.keys()))
        streamlit.experimental_rerun()

# to_be_added_to_unrecent = dict()
# for rpid in master_list:
#     if len(to_be_added_to_unrecent) >= 100:
#         break
#     if rpid not in (unrecent_list):
#         if rpid not in recent_list and rpid not in recent_plays:
#             to_be_added_to_unrecent[rpid] = master_list[rpid]
# if to_be_added_to_unrecent:
#     streamlit.write(f"First {len(to_be_added_to_unrecent)} master tracks to go into unrecent:")
#     for id in to_be_added_to_unrecent:
#         label = f"{master_list[id]['name']} by {master_list[id]['artists'][0]['name']}"
#         url = "https://open.spotify.com/track/{id}"
#         streamlit.markdown(f"[{label}]({url})")
#     sync_to_be_added_to_ur = streamlit.button("Sync these to Not Recently Played")
#     if sync_to_be_added_to_ur:
#         streamlit.write("Attempting to add items to playlist")
#         add_to_playlist(headers, unrecent_playlist, list(to_be_added_to_unrecent.keys()))
#         streamlit.experimental_rerun()
#
# to_be_removed_from_unrecent = dict()
# for rpid in unrecent_list:
#     if rpid in recent_plays or rpid in recent_list:
#         to_be_removed_from_unrecent[rpid] = True
# if to_be_removed_from_unrecent:
#     streamlit.write("Recently played tracks to remove from unrecent:")
#     streamlit.json(to_be_removed_from_unrecent)
#     sync_to_be_removed = streamlit.button("Remove these Recently Played")
#     if sync_to_be_removed:
#         streamlit.write("Attempting to remove items to playlist")
#         remove_from_playlist(headers, unrecent_playlist, list(to_be_removed_from_unrecent.keys()))
#         streamlit.experimental_rerun()
#
# to_be_added_to_master = dict()
# for id in recent_list:
#     if id not in master_list:
#         to_be_added_to_master[id] = recent_list[id]
# if to_be_added_to_master:
#     streamlit.write("Recent tracks not found in master playlist")
#     add_to_master_checks = dict()
#     for id in to_be_added_to_master:
#         label = f"{recent_list[id]['name']} by {recent_list[id]['artists'][0]['name']}"
#         add_to_master_checks[id] = streamlit.checkbox(label)
#
summarize_playlist(recent_playlist, recent_list)
summarize_playlist(unrecent_playlist, unrecent_list)
summarize_playlist(master_playlist, master_list)
# list_playlist(master_playlist, master_list)