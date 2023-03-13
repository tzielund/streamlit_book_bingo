import os

import streamlit
from requests.structures import CaseInsensitiveDict

import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

streamlit.title("Spotify playlist manager")

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
    streamlit.header(playlist_metadata.get("name",plid))
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
compare_playlist_id =  streamlit.sidebar.selectbox("Compare it to:", options=playlist_ids_with_none,
                                              format_func=lambda x: playlist_index.get(x,{'name':""})['name'])
select_playlist_metadata = playlist_index[select_playlist_id]
select_playlist_name = select_playlist_metadata["name"]
select_playlist_list = cache_playlist(headers, select_playlist_id, select_playlist_metadata)
select_playlist_set = set(select_playlist_list.keys())

if compare_playlist_id:
    compare_playlist_metadata = playlist_index[compare_playlist_id]
    compare_playlist_name = compare_playlist_metadata["name"]
    compare_playlist_list = cache_playlist(headers, compare_playlist_id, compare_playlist_metadata)
    compare_playlist_set = set(compare_playlist_list.keys())
else:
    compare_playlist_metadata = {'name':'#NONE'}
    compare_playlist_name = "#NONE"
    compare_playlist_list = dict()
    compare_playlist_set = set()

# Do comparison analytics
playlist_dupes = dict()
for trackid in select_playlist_list.keys():
    dupc = select_playlist_list[trackid].get("duplicate_count", 0)
    if dupc:
        playlist_dupes[trackid] = dupc
shared_tracks = select_playlist_set.intersection(compare_playlist_set)
select_only = select_playlist_set - compare_playlist_set
compare_only = compare_playlist_set - select_playlist_set
union_tracks = select_playlist_set.union(compare_playlist_set)
union_lookup = dict()
for trackid in union_tracks:
    if trackid in select_playlist_list:
        union_lookup[trackid] = select_playlist_list[trackid]
    else:
        union_lookup[trackid] = compare_playlist_list[trackid]

checkmark = "✓"



streamlit.header("Actions")

refresh_list_button = streamlit.button("Refresh the list of playlists")
if refresh_list_button:
    get_cached_playlist_list(headers, ignore_cache=True)
    streamlit.experimental_rerun()

force_refresh_button = streamlit.button(f"Force refresh of {select_playlist_name}")
if force_refresh_button:
    streamlit.write("Caching modified list")
    get_cached_playlist_list(headers, ignore_cache=True)
    cache_playlist(headers, select_playlist_id, select_playlist_metadata, ignore_cache=True)
    clicker = streamlit.button("Click to refresh")
    if not clicker:
        streamlit.stop()
    streamlit.experimental_rerun()

if playlist_dupes:
    remove_dupes_button = streamlit.button(f"Remove {len(playlist_dupes)} duplicates from {select_playlist_name}")
    if remove_dupes_button:
        spotify_util.deduplicate_playlist(headers, select_playlist_metadata, select_playlist_list)
        streamlit.write("Caching modified list")
        get_cached_playlist_list(headers, ignore_cache=True)
        cache_playlist(headers, select_playlist_id, select_playlist_metadata)
        clicker = streamlit.button("Click to refresh")
        if not clicker:
            streamlit.stop()
        streamlit.experimental_rerun()

if compare_only:
    add_from_compare_button = streamlit.button(f"Add {len(compare_only)} from {compare_playlist_name} to {select_playlist_name}")
    if add_from_compare_button:
        streamlit.write("Adding songs...")
        add_to_playlist(headers, select_playlist_metadata, list(compare_only))
        streamlit.write("Caching modified list")
        get_cached_playlist_list(headers, ignore_cache=True)
        cache_playlist(headers, select_playlist_id, select_playlist_metadata)
        clicker = streamlit.button("Click to refresh")
        if not clicker:
            streamlit.stop()
        streamlit.experimental_rerun()

if shared_tracks:
    remove_shared_from_select_button = streamlit.button(f"Remove {len(shared_tracks)} shared tracks from {select_playlist_name}")
    if remove_shared_from_select_button:
        streamlit.write("Removing songs...")
        remove_from_playlist(headers, select_playlist_metadata, list(shared_tracks))
        streamlit.write("Caching modified list")
        get_cached_playlist_list(headers, ignore_cache=True)
        cache_playlist(headers, select_playlist_id, select_playlist_metadata)
        clicker = streamlit.button("Click to refresh")
        if not clicker:
            streamlit.stop()
        streamlit.experimental_rerun()




bunch_sequence = {
    "Shared Tracks": shared_tracks,
    "Select Only": select_only,
    "Compare Only": compare_only
}
streamlit.header("Tracks in selected and compare lists")
rownumber = 1
expanders = list()
for bunch_label in bunch_sequence:
    bunch_set = bunch_sequence[bunch_label]
    bunch_label_with_size = f"{bunch_label} ({len(bunch_set)})"
    expanders.append(streamlit.checkbox(bunch_label_with_size))
    if expanders[-1]:
        for trackid in bunch_set:
            track_details = union_lookup[trackid]
            idxcol, label, isdup = streamlit.columns([1,5,1])
            idxcol.write(rownumber)
            label.write(spotify_util.get_track_markdown(track_details))
            if track_details.get("duplicate_count",0):
                isdup.write(track_details["duplicate_count"])
            rownumber += 1
