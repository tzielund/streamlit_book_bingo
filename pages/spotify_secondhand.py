"""Gets secondhand song data for songs/artists in a playlist."""

import streamlit
from requests.structures import CaseInsensitiveDict
import secondhand_util
import spotify_util
from secondhand_util import SecondhandArtistSearchHtmlParser
from spotify_util import get_cached_playlist_list

streamlit.title("Spotify Secondhand harvest")

KNOWN_ARTIST_MAPPING = secondhand_util.cache_secondhand_streamlit_artist_mapping()

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

select_playlist_id = streamlit.selectbox("Select a playlist", options=playlist_ids,
                                                 format_func=lambda x: playlist_index[x]['name'])
select_playlist_metadata = playlist_index[select_playlist_id]

songlist = spotify_util.cache_playlist(headers, select_playlist_id, select_playlist_metadata)

artist_list = dict()
artist_count = dict()
artist_matched = set()
artist_unmatched = set()
for trackid in songlist:
    track_metadata = songlist[trackid]
    artists = track_metadata.get("artists",[])
    for artist in artists:
        artist_name = artist["name"]
        artist_id = artist["id"]
        if artist_id not in artist_count:
            artist_count[artist_id] = 0
        artist_count[artist_id] += 1
        if artist_id in KNOWN_ARTIST_MAPPING.keys():
            artist_matched.add(artist_id)
        else:
            artist_unmatched.add(artist_id)
        artist_list[artist_id] = artist_name

sorted_unmatched = sorted(artist_unmatched, key=lambda x:artist_count[x], reverse=True)
sorted_matched = sorted(artist_matched, key=lambda x:artist_count[x], reverse=True)

if sorted_unmatched:
    # Match a missing artist and repeat until empty
    select_artist = streamlit.selectbox("Select an artist", options=sorted_unmatched,
                                                format_func=lambda x: artist_list[x])
    select_artist_name = artist_list[select_artist]
    select_artist_search_link = secondhand_util.link_simple_search(select_artist_name)
    streamlit.markdown(f"[{select_artist_name}]({select_artist_search_link})")

    streamlit.write(f"Spotify to Secondhand mapping unknown")
    hrefs = secondhand_util.cache_simple_search(select_artist_name)
    print (hrefs)
    select_artist_match = streamlit.selectbox("Select artist match",
                                              options=list(hrefs.keys()),
                                              format_func=lambda x: hrefs[x])
    set_artist_match_button = streamlit.button("Set this as a match")
    if set_artist_match_button:
        KNOWN_ARTIST_MAPPING[select_artist] = select_artist_match
        secondhand_util.store_secondhand_streamlit_artist_mapping(KNOWN_ARTIST_MAPPING)
        streamlit.experimental_rerun()
    artist_match_override = streamlit.text_input("Override match",value="/artist/XXXX")
    artist_match_override_button = streamlit.button("Set the override")
    if artist_match_override_button:
        KNOWN_ARTIST_MAPPING[select_artist] = artist_match_override
        secondhand_util.store_secondhand_streamlit_artist_mapping(KNOWN_ARTIST_MAPPING)
        streamlit.experimental_rerun()
    streamlit.json(hrefs)

else:
    # Nobody unmatched, so review all the matches
    verify_checkbox = streamlit.checkbox("Verify matches?")
    if verify_checkbox:
        for select_artist in sorted_matched:
            select_artist_name = artist_list[select_artist]
            select_artist_search_link = secondhand_util.link_simple_search(select_artist_name)
            matched_href = KNOWN_ARTIST_MAPPING[select_artist]
            if not matched_href:
                streamlit.markdown(f"* [{select_artist_name}]({select_artist_search_link}) is not matched in Secondhand Songs")
                erase_this = streamlit.button("Try again", key=f"erase_{select_artist}")
                if erase_this:
                    del(KNOWN_ARTIST_MAPPING[select_artist])
                    secondhand_util.store_secondhand_streamlit_artist_mapping(KNOWN_ARTIST_MAPPING)
                    streamlit.experimental_rerun()
            else:
                matched_link = f"https://secondhandsongs.com{matched_href}"
                hrefs = secondhand_util.cache_simple_search(select_artist_name)
                if matched_href in hrefs:
                    matched_name = hrefs[matched_href]
                    streamlit.markdown(f"* [{select_artist_name}]({select_artist_search_link}) "
                                       f"matched to [{matched_name}]({matched_link})")
                    erase_this = streamlit.button("Erase this match", key=f"erase_{select_artist}")
                    if erase_this:
                        del(KNOWN_ARTIST_MAPPING[select_artist])
                        secondhand_util.store_secondhand_streamlit_artist_mapping(KNOWN_ARTIST_MAPPING)
                        streamlit.experimental_rerun()
                else:
                    streamlit.markdown(f"* [{select_artist_name}]({select_artist_search_link}) "
                                       f"matched to: [{matched_href}]({matched_link})")
                    erase_this = streamlit.button("Erase this match", key=f"erase_{select_artist}")
                    if erase_this:
                        del(KNOWN_ARTIST_MAPPING[select_artist])
                        secondhand_util.store_secondhand_streamlit_artist_mapping(KNOWN_ARTIST_MAPPING)
                        streamlit.experimental_rerun()


# All good, let's load covers


streamlit.header("Covers")
select_artist_2 = streamlit.selectbox("Select an artist to see covers", options=sorted_matched,
                                    format_func=lambda x: artist_list[x])
select_artist_name_2 = artist_list[select_artist_2]
select_artist_secondhand_id = KNOWN_ARTIST_MAPPING[select_artist_2]
if select_artist_secondhand_id:
    covers = secondhand_util.cache_covers_list(select_artist_secondhand_id)
    covers
else:
    streamlit.write("Artist not matched for Secondhand Songs")