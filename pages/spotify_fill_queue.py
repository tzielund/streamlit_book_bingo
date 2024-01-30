"""This script populates the queue with songs from a selected playlist."""

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, song_checkbox_group

streamlit.title("Spotify populate queue")

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

# Get list of playlists
playlist_list = get_cached_playlist_list(headers)
playlist_index = dict()
for item in playlist_list:
    playlist_index[item['id']] = item
playlist_ids = list(playlist_index.keys())

# Select a playlist
select_playlist_id = streamlit.sidebar.selectbox("Select a playlist", options=playlist_ids,
                                                 format_func=lambda x: playlist_index[x]['name'])
select_playlist_name = playlist_index[select_playlist_id]['name']
streamlit.header(select_playlist_name)
playlist_metadata = playlist_list[playlist_ids.index(select_playlist_id)]
playlist_tracks = cache_playlist(headers, select_playlist_id, playlist_metadata)

# View the current queue
streamlit.header("Current queue")
show_queue_button = streamlit.checkbox("Show current queue")
if show_queue_button:
    current_queue = spotify_util.get_current_queue(headers)
    for item in current_queue:
        streamlit.markdown(f"* {item['name']} by {item['artists'][0]['name']}")
    streamlit.markdown(f"Total: {len(current_queue)}")
    clear_queue_button = streamlit.button("Clear queue")
    if clear_queue_button:
        for item in current_queue:
            spotify_util.next_track(headers)
        streamlit.experimental_rerun()


# Select a set of songs to add to queue
select_all_button = streamlit.checkbox("Select all")
selected_songs = song_checkbox_group(playlist_tracks, select_all_button)

# Add selected songs to queue
add_to_queue_button = streamlit.button(f"Add {len(selected_songs)} selected songs to queue")
if add_to_queue_button:
    for song_id in selected_songs:
        streamlit.write(f"Adding {playlist_tracks[song_id]['name']}")
        spotify_util.add_track_to_queue(headers, song_id)

