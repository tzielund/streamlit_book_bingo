import json
import os
import re

import streamlit
from requests.structures import CaseInsensitiveDict

import secondhand_util
import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

streamlit.title("Spotify playlist artist analysis")

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

target_playlist_id = streamlit.sidebar.selectbox("Target playlist", options=playlist_ids,
                                                 format_func=lambda x: playlist_index[x]['name'])
target_playlist_metadata = playlist_index[target_playlist_id]
target_playlist_name = target_playlist_metadata["name"]
target_playlist_list = cache_playlist(headers, target_playlist_id, target_playlist_metadata)
target_playlist_set = set(target_playlist_list.keys())

leading_parenthetical = re.compile("^\(.*\)(.*)$")

def normalize_name(raw_name: str) -> str:
    fixed_name = raw_name.strip().casefold()
    if leading_parenthetical.match(fixed_name):
        fixed_name = leading_parenthetical.match(fixed_name).group(1)
    fixed_name = fixed_name.split("(",2)[0]
    fixed_name = fixed_name.split("-",2)[0]
    fixed_name = fixed_name.strip()
    fixed_name = " ".join(fixed_name.split())
    return fixed_name

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

# Pick an artist, any artist
artist_list = list(artist_set)
artist_list.sort(key=lambda x: artist_count[x], reverse=True)
orig_select_artist_id = streamlit.sidebar.radio("Select an artist to consider", options=artist_list,
                                    format_func=lambda x:f"{artist_set[x]} ({artist_count[x]})")
orig_select_artist_name = artist_set[orig_select_artist_id]

streamlit.write(f"Selected artist: {orig_select_artist_name}")
streamlit.header("Similar artists")

related_artists = spotify_util.get_artist_related_artist(headers, orig_select_artist_id)
suggested_artists = dict()
suggested_artists[orig_select_artist_id] = orig_select_artist_name
for related_id in related_artists.keys():
    if related_id not in artist_set:
        suggested_artists[related_id] = related_artists[related_id]["name"]

select_artist_id = streamlit.selectbox("Pick this artist or a similar artist not represented",
                                       options=suggested_artists.keys(),
                                       format_func=lambda x:suggested_artists[x])
select_artist_name = suggested_artists[select_artist_id]

def group_playlist_by_normname(playlist_items):
    result = dict()
    for trackid in playlist_items.keys():
        track_metadata = playlist_items[trackid]
        track_normname = normalize_name(track_metadata["name"])
        if track_normname not in result:
            result[track_normname] = dict()
        result[track_normname][trackid] = track_metadata
    return result

# Locate the songs by this artists
select_artist_playlist_tracks = dict()
for trackid in select_playlist_list.keys():
    track_metadata = select_playlist_list[trackid]
    for artist in track_metadata.get('artists',default_artists):
        if artist["id"] == select_artist_id:
            select_artist_playlist_tracks[trackid] = track_metadata
select_artist_playlist_tracks_by_normname = group_playlist_by_normname(select_artist_playlist_tracks)
select_playlist_normname_set = set(select_artist_playlist_tracks_by_normname.keys())

all_of_them_checkbox = streamlit.checkbox("Show all?")

if all_of_them_checkbox:
    select_artist_top_tracks = spotify_util.get_artist_all_tracks(headers, select_artist_id)
else:
    select_artist_top_tracks = spotify_util.get_artist_top_tracks(headers, select_artist_id)

select_artist_top_tracks_by_normname = group_playlist_by_normname(select_artist_top_tracks)
select_top_normname_set = set(select_artist_top_tracks_by_normname.keys())

playlist_common = select_playlist_normname_set.intersection(select_top_normname_set)
playlist_not_top = select_playlist_normname_set - select_top_normname_set
top_not_playlist = (select_top_normname_set - select_playlist_normname_set) - target_playlist_set

streamlit.header("Set Details")
streamlit.write(f"* Artist top tracks: {len(select_top_normname_set)}")
streamlit.write(f"* Artist playlist tracks: {len(select_playlist_normname_set)}")

streamlit.header("Top tracks in playlist")
playlist_common_sorted = list(playlist_common)
playlist_common_sorted.sort()
for normname in playlist_common_sorted:
    fake_checkbox = streamlit.checkbox(normname, key=f"FakeCheck{normname}", disabled=True, value=True)

show_more_checklist = dict()
add_to_checklist = dict()
num_to_add = 0
list_to_add = list()
streamlit.header("Top tracks not in playlist")
# streamlit.json(list(top_not_playlist))
top_not_playlist_sorted = list(top_not_playlist)
top_not_playlist_sorted.sort(key=lambda x:len(select_artist_top_tracks_by_normname[x]), reverse=True)
for normname in top_not_playlist_sorted:
    detailed_list = select_artist_top_tracks_by_normname[normname]
    show_more_checklist[normname] = streamlit.checkbox(f"{normname} ({len(detailed_list)})", key=f"AddCheck{normname}")
    if show_more_checklist[normname]:
        for trackid in detailed_list:
            track_metadata = select_artist_top_tracks[trackid]
            trackname = track_metadata['name']
            print(f"Showing {trackname} from {json.dumps(track_metadata)}")
            add_to_checklist[trackid] = streamlit.checkbox(f"add + {trackname}", key=f'add_{trackid}')
            if add_to_checklist[trackid]:
                num_to_add += 1
                list_to_add.append(trackid)

add_them = streamlit.button(f"Add these {num_to_add} to {target_playlist_name}",disabled=not(num_to_add))

if add_them:
    # specifics_to_add = list()
    # for normname in list_to_add:
    #     specifics_to_add.extend(select_artist_top_tracks_by_normname[normname].keys())
    print ("Adding...")
    spotify_util.add_to_playlist(headers, target_playlist_metadata, list_to_add)
    spotify_util.get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()


remove_from_checklist = dict()
num_to_remove = 0
streamlit.header("Playlist deep tracks")
list_to_remove = list()
for normname in playlist_not_top:
    remove_from_checklist[normname] = streamlit.checkbox(normname, key=f"RemoveCheck{normname}")
    if remove_from_checklist[normname]:
        num_to_remove += 1
        list_to_remove.append(normname)

remove_them = streamlit.button(f"Remove from {select_playlist_name} and add to {target_playlist_name}",
                                   disabled=not(num_to_remove))
if remove_them:
    actual_to_remove = list()
    for normname in list_to_remove:
        track_details = select_artist_playlist_tracks_by_normname[normname]
        trackids = track_details.keys()
        actual_to_remove.extend(trackids)
    remove_from_playlist(headers, select_playlist_metadata, actual_to_remove)
    add_to_playlist(headers, target_playlist_metadata, actual_to_remove)
    # get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()



#
# streamlit.header(f"Playlist Tracks for {select_artist_name}")
# list_tracklist(select_artist_playlist_tracks)
#
# streamlit.header(f"Top Tracks for {select_artist_name}")
# list_tracklist(select_artist_top_tracks)
#
