import os

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

default_artists = [{'name':'no name'}]


streamlit.title("Spotify playlist near duplicate locator")

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

def list_tracklist(playlist_tracks):
    default_artists = [{'name':'no name'}]
    for trackid in playlist_tracks.keys():
        item = playlist_tracks[trackid]
        label = f"{item['name']} by {item.get('artists',default_artists)[0]['name']}"
        url = f"https://open.spotify.com/track/{trackid}"
        streamlit.markdown(f"* [{label}]({url})")


playlist_list = get_cached_playlist_list(headers)
playlist_index = dict()
for item in playlist_list:
    playlist_index[item['id']] = item
playlist_ids = list(playlist_index.keys())
playlist_ids_with_none = list()
playlist_ids_with_none.append("")
playlist_ids_with_none.extend(playlist_ids)
select_playlist_id = streamlit.sidebar.selectbox("Select a playlist", options=playlist_ids,
                                                 format_func=lambda x: playlist_index[x]['name'])
select_playlist_metadata = playlist_index[select_playlist_id]
select_playlist_name = select_playlist_metadata["name"]
select_playlist_list = cache_playlist(headers, select_playlist_id, select_playlist_metadata)
select_playlist_set = set(select_playlist_list.keys())

require_artist_match = streamlit.sidebar.checkbox("Require artist match")

def normalize_name(raw_name: str) -> str:
    raw_name = raw_name.split("(",2)[0]
    raw_name = raw_name.split("-",2)[0]
    return raw_name.casefold()

norm_name_matches = dict()
for trackid in select_playlist_list.keys():
    track_metadata = select_playlist_list[trackid]
    track_name_raw = track_metadata["name"]
    track_name_norm = normalize_name(track_name_raw)
    if require_artist_match:
        track_name_norm = f"{track_name_norm} by {track_metadata.get('artists',default_artists)[0]['name']}"
    if track_name_norm not in norm_name_matches:
        norm_name_matches[track_name_norm] = dict()
    norm_name_matches[track_name_norm][trackid] = track_metadata

name_list_sorted = list(norm_name_matches.keys())
name_list_sorted.sort()


streamlit.header("Near matches in this playlist")
to_be_deleted = dict()
for name in name_list_sorted:
    if len(norm_name_matches[name]) > 1:
        streamlit.subheader(name)
        playlist_tracks = norm_name_matches[name]

        for trackid in playlist_tracks.keys():
            item = playlist_tracks[trackid]
            label = f"{item['name']} by {item.get('artists',default_artists)[0]['name']}"
            url = f"https://open.spotify.com/track/{trackid}"
            to_be_deleted[trackid] = streamlit.checkbox(label, key=f'del{trackid}')

selected = 0
to_be_deleted_trackids = dict()
for trackid in to_be_deleted.keys():
    if to_be_deleted[trackid]:
        selected += 1
        to_be_deleted_trackids[trackid] = select_playlist_list[trackid]
if selected:
    streamlit.write("Selected to delete:")
    list_tracklist(to_be_deleted_trackids)
    do_it = streamlit.button("Do it!")
    if do_it:
        spotify_util.remove_from_playlist(headers, select_playlist_metadata, list(to_be_deleted_trackids.keys()))
        get_cached_playlist_list(headers, ignore_cache=True)
        streamlit.experimental_rerun()
