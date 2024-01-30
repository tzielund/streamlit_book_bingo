import json
import os
import re

import streamlit
from requests.structures import CaseInsensitiveDict

import secondhand_util
import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

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

streamlit.title("Spotify playlist artist analysis")

playlist_list = get_cached_playlist_list(headers)
playlist_choice = streamlit.sidebar.selectbox("Select a playlist", playlist_list, format_func=lambda x: x["name"])

playlist_id = playlist_choice["id"]

select_playlist_list = cache_playlist(headers, playlist_id, playlist_choice)

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

# Sort the artists by number of tracks
sorted_artists = sorted(artist_set.keys(), key=lambda x:artist_count[x], reverse=True)

select_artist_id = streamlit.sidebar.radio("Select an artist", sorted_artists,
                                           format_func=lambda x: f"{artist_set[x]} ({artist_count[x]})")

# fetch the top 10 tracks for this artist
select_artist_top_tracks = spotify_util.get_artist_top_tracks(headers, select_artist_id)

# Locate the songs by this artists in the selected playlist
select_artist_playlist_tracks = dict()
for trackid in select_playlist_list.keys():
    track_metadata = select_playlist_list[trackid]
    for artist in track_metadata.get('artists',default_artists):
        if artist["id"] == select_artist_id:
            select_artist_playlist_tracks[trackid] = track_metadata

streamlit.subheader(f"Playlist {playlist_choice['name']} has {len(select_artist_playlist_tracks)} tracks by {artist_set[select_artist_id]}")
refresh_playlist_button = streamlit.button("Refresh playlist?")
if refresh_playlist_button:
    select_playlist_list = cache_playlist(headers, playlist_id, playlist_choice, ignore_cache=True)
    streamlit.experimental_rerun()

# List the top tracks in the selected playlist as checkboxes
streamlit.header("Top tracks that are in the playlist (check to remove)")
checked_top_tracks_to_remove = list()
for trackid in select_artist_top_tracks:
    if trackid in select_artist_playlist_tracks.keys():
        track = select_artist_top_tracks[trackid]
        this_checkbox = (streamlit.checkbox(f'{track["name"]} {trackid}'))
        if this_checkbox:
            play_it_button = streamlit.button(f"Play {trackid}")
            if play_it_button:
                spotify_util.add_track_to_queue(headers, trackid)
                spotify_util.next_track(headers)
            checked_top_tracks_to_remove.append(trackid)

# List the top tracks NOT in the selected playlist as checkboxes
streamlit.header("Top tracks that are NOT in the playlist (check to add)")
checked_top_tracks_to_add = list()
for trackid in select_artist_top_tracks:
    if trackid not in select_artist_playlist_tracks.keys():
        track = select_artist_top_tracks[trackid]
        this_checkbox = (streamlit.checkbox(f'{track["name"]} {trackid}'))
        if this_checkbox:
            play_it_button = streamlit.button(f"Play {trackid}")
            if play_it_button:
                spotify_util.add_track_to_queue(headers, trackid)
                spotify_util.next_track(headers)
            checked_top_tracks_to_add.append(trackid)


# Non top-tracks in the playlist
streamlit.header("Non top tracks in the playlist (check to remove)")
checked_non_top_tracks_to_add = list()
sorted_by_name = sorted(select_artist_playlist_tracks.keys(), key=lambda x:select_artist_playlist_tracks[x]['name'])
for trackid in sorted_by_name:
    if trackid not in select_artist_top_tracks.keys():
        track = select_artist_playlist_tracks[trackid]
        this_checkbox = (streamlit.checkbox(f'{track["name"]} {trackid}'))
        if this_checkbox:
            play_it_button = streamlit.button(f"Play {trackid}")
            if play_it_button:
                spotify_util.add_track_to_queue(headers, trackid)
                spotify_util.next_track(headers)
            checked_non_top_tracks_to_add.append(trackid)

if checked_top_tracks_to_add or checked_top_tracks_to_remove or checked_non_top_tracks_to_add:
    streamlit.header("Verify changes")
    for trackid in checked_top_tracks_to_remove:
        track = select_artist_top_tracks[trackid]
        streamlit.write(f"Remove {track['name']} {trackid}")
    for trackid in checked_top_tracks_to_add:
        track = select_artist_top_tracks[trackid]
        streamlit.write(f"Add {track['name']} {trackid}")
    for trackid in checked_non_top_tracks_to_add:
        track = select_playlist_list[trackid]
        streamlit.write(f"Remove {track['name']} {trackid}")
    verify_button = streamlit.button("Do it!")
    if verify_button:
        if checked_top_tracks_to_remove:
            remove_from_playlist(headers, playlist_id, checked_top_tracks_to_remove)
        if checked_top_tracks_to_add:
            add_to_playlist(headers, playlist_id, checked_top_tracks_to_add)
        if checked_non_top_tracks_to_add:
            remove_from_playlist(headers, playlist_id, checked_non_top_tracks_to_add)

        streamlit.experimental_rerun()
