import os

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
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
if token != bearer:
    streamlit.session_state["spotify_bearer"] = token
    streamlit.experimental_rerun()

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

# Optional Refresh Actions
redo_playlist_button = streamlit.sidebar.button("Reload playist list")
if redo_playlist_button:
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()
refresh_rp = streamlit.sidebar.button("Reload recently played")
if refresh_rp:
    get_recently_played(headers, ignore_cache=True)
    streamlit.experimental_rerun()

total_playlist_name = "master playlist"
sofar_playlist_name = "Recently Played"
remaining_playlist_name = "not recently played"

for playlist in playlist_list:
    if playlist["name"] == total_playlist_name:
        total_playlist = playlist
    if playlist["name"] == remaining_playlist_name:
        remaining_playlist = playlist
    if playlist["name"] == sofar_playlist_name:
        sofar_playlist = playlist

# Recently Played
recent_play_list = get_recently_played(headers)
recent_play_set = set(recent_play_list.keys())

# Load other playlists
total_id = total_playlist['id']
total_list = cache_playlist(headers, total_id, total_playlist)
total_set = set(total_list.keys())

sofar_id = sofar_playlist['id']
sofar_list = cache_playlist(headers, sofar_id, sofar_playlist)
sofar_set = set(sofar_list.keys())

remaining_id = remaining_playlist['id']
remaining_list = cache_playlist(headers, remaining_id, remaining_playlist)
remaining_set = set(remaining_list.keys())




streamlit.header("What needs to be done")
# """
# In order of priority
# $RECENT +=> RP
# RP -=> NRP
# Master playlist should be equal to the union of rp and nrp
# rp should have everything from $RECENT
# nrp should be disjoint from rp
# """

# Recently played tracks that should be added to the played-so-far playlist and
# removed from remaining playlist
recent_to_add_set = (recent_play_set - sofar_set).intersection(total_set)
recent_to_add_button = streamlit.button(
    f"Add {len(recent_to_add_set)} recently played to {sofar_playlist_name}",
    disabled=not(recent_to_add_set)
)
spotify_util.write_track_list(recent_play_list, recent_to_add_set)
if recent_to_add_button:
    spotify_util.add_to_playlist(headers, sofar_playlist, recent_to_add_set)
    spotify_util.remove_from_playlist(headers, remaining_playlist, recent_to_add_set)
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()

# Double-check if there are any so-far played tracks still in the remaining list
sofar_to_remove_set = sofar_set.intersection(remaining_set)
sofar_to_remove_button = streamlit.button(
    f"Remove {len(sofar_to_remove_set)} already played from {remaining_playlist_name}",
    disabled=not(sofar_to_remove_set)
)
spotify_util.write_track_list(sofar_list, sofar_to_remove_set)
if sofar_to_remove_button:
    spotify_util.remove_from_playlist(headers, remaining_playlist, sofar_to_remove_set)
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()

# Verify all the stuff in remaining is still found in the total list
remaining_to_remove = remaining_set - total_set
remaining_to_remove_button = streamlit.button(
    f"Remove {len(remaining_to_remove)} from {remaining_playlist_name} that aren't in {total_playlist_name}",
    disabled=not(remaining_to_remove)
)
spotify_util.write_track_list(remaining_list, remaining_to_remove)
if remaining_to_remove_button:
    spotify_util.remove_from_playlist(headers, remaining_playlist, remaining_to_remove)
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()

# Verify all of the total set is either in so-far or ramaining
unaccounted = (total_set - sofar_set) - remaining_set
unacounted_button = streamlit.button(
    f"Add {len(unaccounted)} to {remaining_playlist_name} unaccounted from {total_playlist_name}",
    disabled=not(unaccounted)
)
spotify_util.write_track_list(total_list, unaccounted)
if unacounted_button:
    spotify_util.add_to_playlist(headers, remaining_playlist, unaccounted)
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()

# Verify that remaining playlist does not include any tracks (no longer) in total
no_longer_set = (remaining_set - total_set)
no_longer_button = streamlit.button(
    f"Remove {len(no_longer_set)} from {remaining_playlist_name} (not present in) {total_playlist_name}",
    disabled=not(no_longer_set)
)
spotify_util.write_track_list(remaining_list, no_longer_set)
if no_longer_button:
    spotify_util.remove_from_playlist(headers, remaining_playlist, no_longer_set)
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()




summarize_playlist({'id':"$RECENT", 'tracks':{'total':len(recent_play_set)}}, recent_play_list)
list_recent_check = streamlit.checkbox("Show recent plays")
if list_recent_check:
    spotify_util.write_track_list(recent_play_list)

summarize_playlist(sofar_playlist, sofar_list)
list_sofar_check = streamlit.checkbox(f"Show {sofar_playlist_name}")
if list_sofar_check:
    spotify_util.write_track_list(sofar_list)

summarize_playlist(remaining_playlist, remaining_list)
list_remaining_check = streamlit.checkbox(f"Show {remaining_playlist_name}")
if list_remaining_check:
    spotify_util.write_track_list(remaining_list)

summarize_playlist(total_playlist, total_list)
list_total_check = streamlit.checkbox(f"Show {total_playlist_name}")
if list_total_check:
    spotify_util.write_track_list(total_list)
