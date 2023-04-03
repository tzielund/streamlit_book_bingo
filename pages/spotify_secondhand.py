"""Gets secondhand song data for songs/artists in a playlist."""

import streamlit
from requests.structures import CaseInsensitiveDict

import secondhand_util
import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

streamlit.title("Spotify Secondhand harvest")

headers = CaseInsensitiveDict()
headers["Authorization"] = "none"
headers["Content-Type"] = "application/json"

sheader = CaseInsensitiveDict()
sheader["Accept"] = "application/json"

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

songlist = spotify_util.cache_playlist(headers, select_playlist_id, select_playlist_metadata)

artist_list = dict()
for trackid in songlist:
    track_metadata = songlist[trackid]
    artists = track_metadata.get("artists",[])
    for artist in artists:
        artist_name = artist["name"]
        artist_id = artist["id"]
        artist_list[artist_id] = artist_name

select_artist = streamlit.sidebar.selectbox("Select an artist", options=list(artist_list.keys()),
                                            format_func=lambda x: artist_list[x])
select_artist_name = artist_list[select_artist]
select_artist_search_link = secondhand_util.link_simple_search(select_artist_name)
streamlit.markdown(f"[{select_artist_name}]({select_artist_search_link})")

artist_search = secondhand_util.cache_simple_search(select_artist_name)
streamlit.markdown(f"<pre>{artist_search}</pre>")
artist_search
