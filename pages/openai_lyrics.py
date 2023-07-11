import os
import json
import streamlit
from requests.structures import CaseInsensitiveDict
import openai

import spotify_util
from spotify_util import get_cached_playlist_list, cache_playlist, get_recently_played, add_to_playlist, \
    remove_from_playlist, CACHE_DIR

streamlit.title("Song Lyrics Checker with OpenAI")

streamlit.header("Authentication")


streamlit.write("Paste in your OpenAI secret key")
bearer = ""
if "openai_key" in streamlit.session_state:
    bearer = streamlit.session_state["openai_key"]
openai_key = streamlit.text_input("Paste in secret key", value=bearer)
if not openai_key:
    streamlit.stop()
if openai_key != bearer:
    streamlit.session_state["openai_key"] = openai_key
    streamlit.experimental_rerun()

openai.organization = "org-uk8kYQBBMTo6qpfoifBJZ1Xp"
openai.api_key = openai_key

trackid = "5HNCy40Ni5BZJFw1TKzRsC"
title = "Comfortably Numb"
artist = "Pink Floyd"

headers = {}

playlist_list = get_cached_playlist_list(headers)
playlist_index = dict()
for item in playlist_list:
    playlist_index[item['id']] = item
playlist_ids = list(playlist_index.keys())
playlist_ids_with_none = list()
playlist_ids_with_none.append("")
playlist_ids_with_none.extend(playlist_ids)
select_playlist_id = streamlit.selectbox("Select a playlist", options=playlist_ids,
                                         format_func=lambda x: playlist_index[x]['name'])
select_playlist_metadata = playlist_index[select_playlist_id]
select_playlist_name = select_playlist_metadata["name"]
select_playlist_list = cache_playlist(headers, select_playlist_id, select_playlist_metadata)
select_playlist_set = set(select_playlist_list.keys())
select_playlist_labels = dict()
for trackid in select_playlist_set:
    track_metadata = select_playlist_list[trackid]
    select_playlist_labels[trackid] = spotify_util.get_track_label(track_metadata)


select_track_id = streamlit.selectbox("Select a song from it", options=select_playlist_set,
                                      format_func=lambda x: select_playlist_labels[x])

def cache_song_lyrics_recitation(api_key, trackid, title_artist):
    filename = f"openai_cache/lyrics/{trackid}.json"
    if os.path.exists(filename):
        with open (filename) as IN:
            return json.load(IN)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"What are the lyrics to {title_artist}?"}
        ]
    )
    with open (filename, 'w') as OUT:
        OUT.write(json.dumps(response, indent=4))
    return response

response = cache_song_lyrics_recitation(openai_key, select_track_id, select_playlist_labels[select_track_id])
response["choices"][0]["message"]["content"]