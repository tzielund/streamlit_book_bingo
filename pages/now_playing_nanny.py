"""Checks whether the currently playing song is in the "not recently played" list."""

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
from spotify_util import get_cached_playlist_list

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

playlist_list = get_cached_playlist_list(headers)
remaining_playlist_name = "not recently played"
remaining_playlist = None
for playlist in playlist_list:
    if playlist["name"] == remaining_playlist_name:
        remaining_playlist = playlist
if not remaining_playlist:
    streamlit.write(f"Could not find {remaining_playlist_name} playlist")
    streamlit.stop()

remaining_id = remaining_playlist['id']
remaining_list = spotify_util.cache_playlist(headers, remaining_id, remaining_playlist)
remaining_set = set(remaining_list.keys())

# Get the currently playing song
currently_playing = spotify_util.get_current_playing_track(headers)
currently_playing_id = currently_playing["item"]["id"]
currently_playing_name = currently_playing["item"]["name"]
currently_playing_artist = currently_playing["item"]["artists"][0]["name"]
if currently_playing_id in remaining_set:
    streamlit.write(f"Good Song: {currently_playing_name} by {currently_playing_artist} is in {remaining_playlist_name}")
else:
    streamlit.write(f"Repeat!  {currently_playing_name} by {currently_playing_artist}")


# List the not recently played songs
streamlit.header("Not Recently Played")
for trackid in remaining_list.keys():
    item = remaining_list[trackid]
    label = f"{item['name']} by {item['artists'][0]['name']}"
    url = f"https://open.spotify.com/track/{trackid}"
    streamlit.markdown(f"* [{label}]({url})")