import json
import os
import re
import time

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

streamlit.title("Spotify playlist similar-artist analysis")

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




#
# def summarize_playlist(playlist_metadata, playlist_tracks):
#     plid = playlist_metadata['id']
#     streamlit.header(playlist_metadata.get("name",plid))
#     streamlit.write(f"Total: {playlist_metadata['tracks']['total']}")
#     # for trackid in playlist_tracks.keys():
#     #     item = playlist_tracks[trackid]
#     #     streamlit.markdown(f"* {item['name']}")
#
def list_tracklist(playlist_tracks):
    # streamlit.json(playlist_tracks)
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

default_artists = [{'name':'no name','id':0}]

# Build a list of artists
artist_set = dict()
artist_count = dict()
for trackid in select_playlist_list.keys():
    track_metadata = select_playlist_list[trackid]
    for artist in track_metadata.get('artists',default_artists):
        if artist['id']:
            aid = artist['id']
            artist_set[aid] = artist['name']
            if aid not in artist_count:
                artist_count[aid] = 0
            artist_count[aid] += 1

streamlit.write(f"Found {len(artist_set)} different artists in this playlist.")

related_set = dict()
related_metadata = dict()
raprog = streamlit.progress(0.0)
so_far = 0
for artist_id in artist_set:
    related_dict = spotify_util.get_artist_related_artist(headers, artist_id)
    for related_id in related_dict.keys():
        if related_id not in artist_set:
            related_metadata[related_id] = related_dict[related_id]
            if related_id not in related_set:
                related_set[related_id] = 0
            related_set[related_id] += 1
    so_far += 1
    raprog.progress(so_far/len(artist_set))

streamlit.write(f"Recommendations contain {len(related_set)} artists")

related_top = list(related_set.keys())
related_top.sort(key=lambda x:related_set[x], reverse=True)

related_top = related_top[0:100]
more_about_artist = dict()
adding_track_checks = dict()
adding_tracks_list = list()
for related_id in related_top:
    related_artist = related_metadata[related_id]["name"]
    more_about_artist[related_id] = streamlit.checkbox(related_artist, key=f"more_{related_id}")
    if more_about_artist[related_id]:
        streamlit.markdown(f"* [{related_artist}](https://open.spotify.com/artist/{related_id}) ({related_set[related_id]})")
        hits = spotify_util.get_artist_top_tracks(headers, related_id)
        for trackid in hits.keys():
            trackname = hits[trackid]["name"]
            if trackid not in adding_track_checks:
                adding_track_checks[trackid] = streamlit.checkbox(f"Add {trackname}", key=f"add_{trackid}")
                if adding_track_checks[trackid]:
                    adding_tracks_list.append(trackid)

add_them = streamlit.button(f"Add {len(adding_tracks_list)} songs to {select_playlist_name}")
if add_them:
    spotify_util.add_to_playlist(headers, select_playlist_metadata, adding_tracks_list)
    spotify_util.get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()