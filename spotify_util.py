# Spotify utils

import json
import os
import time

import dateutil.parser
import requests
import streamlit

CACHE_DIR = "spotify_cache/"
os.makedirs(CACHE_DIR, exist_ok=True)

PLAYLIST_CACHE_DIR = f"{CACHE_DIR}playlists/"
os.makedirs(PLAYLIST_CACHE_DIR, exist_ok=True)

ARTIST_TOP_CACHE_DIR = f"{CACHE_DIR}artist_top/"
os.makedirs(ARTIST_TOP_CACHE_DIR, exist_ok=True)

ARTIST_ALBUMS_CACHE_DIR = f"{CACHE_DIR}artist_albums/"
os.makedirs(ARTIST_ALBUMS_CACHE_DIR, exist_ok=True)

ALBUM_TRACKS_CACHE_DIR = f"{CACHE_DIR}album_tracks/"
os.makedirs(ALBUM_TRACKS_CACHE_DIR, exist_ok=True)

ARTIST_ALL_TRACKS_CACHE_DIR = f"{CACHE_DIR}artist_all_tracks/"
os.makedirs(ARTIST_ALL_TRACKS_CACHE_DIR, exist_ok=True)

special_playlist_recent = "$RECENT_100"
special_playlist_liked = "$LIKED"

def get_cached_playlist_list(headers, ignore_cache=False):
    cache_filename = f"{PLAYLIST_CACHE_DIR}playlist_list.json"
    if not ignore_cache and os.path.exists(cache_filename):
        with open (cache_filename) as IN:
            return json.load(IN)
    result = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    if result.status_code != 200:
        streamlit.write(result.status_code)
        streamlit.write(result.text)
        streamlit.stop()
    items = result.json()["items"]
    special_recent = {
        "id": special_playlist_recent,
        "name": special_playlist_recent
    }
    items.append(special_recent)
    special_recent = {
        "id": special_playlist_liked,
        "name": special_playlist_liked
    }
    items.append(special_recent)
    with open (cache_filename, 'w') as OUT:
        OUT.write(json.dumps(items, indent=4))
    return items


def index_playlist(playlist_full):
    """Reformats tracks as a simple dict of trackId->{name, [{artistId, artistName}]}"""
    result = dict()
    for item in playlist_full:
        track = item.get("track",{})
        if not track:
            continue
        id = track.get("id")
        name = track.get("name")
        artists = list()
        for artstr in track.get("artists",[]):
            artists.append({
                "id": artstr.get("id","no_id"),
                "name": artstr.get("name","no_name")
            })
        if id in result:
            result[id]["duplicate_count"] += 1
        else:
            result[id] = {
                "id": id,
                "name": name,
                "artists": artists,
                "duplicate_count": 0
            }
    return result

def cache_playlist(headers, playlist_id, playlist_metadata, ignore_cache=False):
    """Gets all items from the given playlist either from cache or from the API."""
    if playlist_id == special_playlist_recent:
        return get_recently_played(headers, ignore_cache)
    if playlist_id == special_playlist_liked:
        return get_liked(headers, ignore_cache)
    new_snapshot = playlist_metadata["snapshot_id"]
    playlist_file = CACHE_DIR + playlist_id + ".json"
    playlist_raw_file = CACHE_DIR + playlist_id + "_RAW.json"
    if not ignore_cache and os.path.exists(playlist_file):
        with open (playlist_file) as IN:
            playlist_details = json.load(IN)
            cached_snapshot = playlist_details["snapshot_id"]
            if cached_snapshot == new_snapshot:
                print(f"Cached {playlist_id} is still valid")
                return playlist_details["items"]
    # If here, we must extract the full playlist and cache it
    streamlit.write(f"Caching playlist {playlist_metadata['name']}")
    prog = streamlit.progress(0.0)
    total = playlist_metadata['tracks']['total']+1
    playlist_tracks = list()
    done = False
    offset = 0
    pagesize = 100
    print(f"Preparing to extract {playlist_id}")
    while not done:
        print (f"Offset {offset}")
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        url += f"?offset={offset}&limit={pagesize}"
        print (url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            response.status_code
            response.text
            return
        jsondata = response.json()
        # streamlit.json(jsondata)
        itemlist = jsondata["items"]
        progval = min(len(playlist_tracks)/total,1.0)
        prog.progress(progval)
        print (f"Found {len(itemlist)}")
        playlist_tracks.extend(itemlist)
        if len(itemlist) < pagesize:
            done = True
        offset += pagesize
        time.sleep(2)
    playlist_metadata["items"] = index_playlist(playlist_tracks)
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(playlist_metadata, indent=4))
    with open(playlist_raw_file, 'w') as OUT:
        playlist_metadata["raw_items"] = playlist_tracks
        OUT.write(json.dumps(playlist_metadata, indent=4))
    return cache_playlist(headers, playlist_id, playlist_metadata)

def get_liked(headers, ignore_cache=False):
    """Looks for liked/saved tracks either from cache or API and returns a playlist-like index list."""
    recent_cache_filename = f"{PLAYLIST_CACHE_DIR}liked_list.json"
    if not ignore_cache and os.path.exists(recent_cache_filename):
        with open (recent_cache_filename) as IN:
            return json.load(IN)
    recent_list = list()
    done = False
    liked_url = f"https://api.spotify.com/v1/me/tracks"
    while not done:
        params = {"limit":50}
        print (f"{liked_url} and we have {len(recent_list)}")

        recent_result = requests.get(liked_url, headers=headers, params=params)
        # recent_result.status_code
        if recent_result.status_code != 200:
            recent_result.text
        recent_json = recent_result.json()
        print(json.dumps(recent_json,indent=2))
        recent_items = recent_json["items"]
        for item in recent_items:
            # streamlit.json(item)
            track = item["track"]
            if 'id' not in track:
                print ("What the...")
                print (json.dumps(item, indent=2))
                continue
            recent_list_struct = dict()
            recent_list_struct["id"] = track["id"]
            recent_list_struct["name"] = track["name"]
            recent_list_struct['artists'] = track.get("artists",[])
            recent_list.append(recent_list_struct)
        if len(recent_list) > 200 or len(recent_items) == 0:
            break
        liked_url = recent_json["next"]
        if not liked_url:
            break
    recent_index = dict()
    for item in recent_list:
        itemid = item["id"]
        recent_index[itemid] = item
    with open(recent_cache_filename, 'w') as OUT:
        OUT.write(json.dumps(recent_index, indent=4))
    return recent_index


def get_recently_played(headers, ignore_cache=False):
    """Looks for recent tracks either from cache or API and returns a playlist-like index list."""
    recent_cache_filename = f"{PLAYLIST_CACHE_DIR}recent_list.json"
    if not ignore_cache and os.path.exists(recent_cache_filename):
        with open (recent_cache_filename) as IN:
            return json.load(IN)
    recent_list = list()
    done = False
    oldest = None
    recent_url = f"https://api.spotify.com/v1/me/player/recently-played"
    while not done:
        params = {"limit":50}
        print (f"{recent_url} and we have {len(recent_list)}")

        recent_result = requests.get(recent_url, headers=headers, params=params)
        # recent_result.status_code
        if recent_result.status_code != 200:
            recent_result.text
        recent_json = recent_result.json()
        print(json.dumps(recent_json,indent=2))
        recent_items = recent_json["items"]
        for item in recent_items:
            # streamlit.json(item)
            track = item["track"]
            if 'id' not in track:
                print ("What the...")
                print (json.dumps(item, indent=2))
                continue
            recent_list_struct = dict()
            recent_list_struct["id"] = track["id"]
            recent_list_struct["name"] = track["name"]
            recent_list_struct['artists'] = track.get("artists",[])
            pAt = item["played_at"]
            pAtDt = dateutil.parser.isoparse(pAt)
            pAtTs = int(round(pAtDt.timestamp()))
            oldest = pAtTs
            recent_list_struct["played_at"] = pAt
            recent_list_struct["played_at_timestamp"] = pAtTs
            recent_list.append(recent_list_struct)
        if len(recent_list) > 200 or len(recent_items) == 0:
            break
        recent_url = recent_json["next"]
    recent_index = dict()
    for item in recent_list:
        itemid = item["id"]
        recent_index[itemid] = item
    with open(recent_cache_filename, 'w') as OUT:
        OUT.write(json.dumps(recent_index, indent=4))
    return recent_index

def add_to_playlist(headers, playlist_metadata, idlist):
    """Tries to add the given list of items to the specified playlist."""
    plid = playlist_metadata['id']
    url = f"https://api.spotify.com/v1/playlists/{plid}/tracks"
    all_uris = list()
    for id in idlist:
        all_uris.append(f"spotify:track:{id}")
    print (f"Starting to add {len(all_uris)}")
    while len(all_uris) > 0:
        if len(all_uris) > 100:
            uris = all_uris[0:100]
            all_uris = all_uris[100:]
            print (f"Trying first 100, leaving {len(all_uris)} for later")
        else:
            uris = all_uris
            all_uris = []
        data={"uris":uris}
        result = requests.post(url, data=json.dumps(data), headers=headers)
        if result.status_code != 201:
            print(result.status_code)
            print(result.text)
            raise (RuntimeError("Couldn't update playlist"))

def remove_from_playlist(headers, playlist_metadata, idlist):
    """Tries to remove the given list of items from the specified playlist."""
    plid = playlist_metadata['id']
    print(f"Removing {len(idlist)} tracks from {playlist_metadata['name']}")
    url = f"https://api.spotify.com/v1/playlists/{plid}/tracks"
    all_uris = list()
    for id in idlist:
        all_uris.append(f"spotify:track:{id}")
    while len(all_uris) > 0:
        if len(all_uris) > 100:
            uris = all_uris[0:100]
            all_uris = all_uris[100:]
        else:
            uris = all_uris
            all_uris = []
        print(f"Removing {len(uris)}, leaving {len(all_uris)}")
        data={"uris":uris}
        result = requests.delete(url, data=json.dumps(data), headers=headers)
        if result.status_code != 200:
            print(result.status_code)
            print(result.text)
            raise (RuntimeError("Couldn't update playlist"))

def deduplicate_playlist(headers, playlist_metadata, playlist_track_index):
    """Removes tracks in excess of one copy of each."""
    to_be_removed = list()
    for trackid in playlist_track_index:
        item = playlist_track_index[trackid]
        for i in range(0,item.get("duplicate_count",0)):
            to_be_removed.append(trackid)
    if to_be_removed:
        remove_from_playlist(headers, playlist_metadata, to_be_removed)

def get_track_label(track_details) -> str:
    """Returns '{name} by {artist...}"""
    track_name = track_details['name']
    track_artist = track_details['artists'][0]['name']
    track_label = f"{track_name} by {track_artist}"
    return track_label

def get_track_url(trackid) -> str:
    return f"https://open.spotify.com/track/{trackid}"

def get_track_markdown(track_details) -> str:
    return f"[{get_track_label(track_details)}]({get_track_url(track_details['id'])})"

def write_track_list(track_list, include_set:set = None, context=streamlit):
    if include_set is None:
        include_set = set(track_list.keys())
    rownumber = 0
    for trackid in include_set:
        track_details = track_list.get(trackid)
        if track_details:
            context.write(f"{rownumber}: {get_track_markdown(track_details)}")
        else:
            context.write(f"{rownumber}: {trackid} (not found)")
        rownumber += 1

def get_artist_top_tracks(headers, artist_id, ignore_cache=False):
    """Gets top tracks for given artist from cache or from the API."""
    playlist_file = ARTIST_TOP_CACHE_DIR + artist_id + ".json"
    if not ignore_cache and os.path.exists(playlist_file):
        with open (playlist_file) as IN:
            playlist_details = json.load(IN)
            return playlist_details
    # If here, we must extract the full playlist and cache it
    streamlit.write(f"Caching artist top tracks for {artist_id}")
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
    # url = f"https://api.spotify.com/v1/search?fear+artist:{artist_id}"
    print (url)
    response = requests.get(url, headers=headers)
    print (f"done {response.status_code}")
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        raise RuntimeError(f"Problem getting top tracks for {artist_id}")
    jsondata = response.json()
    itemlist = jsondata["tracks"]
    tracklist = list()
    for item in itemlist:
        trackwrapper = dict()
        trackwrapper["track"] = item
        tracklist.append(trackwrapper)
    playlist_metadata = index_playlist(tracklist)
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(playlist_metadata, indent=4))
    return playlist_metadata

def get_artist_albums(headers, artist_id, ignore_cache=False):
    """Gets a list of albums for the artist"""
    playlist_file = ARTIST_ALBUMS_CACHE_DIR + artist_id + ".json"
    if not ignore_cache and os.path.exists(playlist_file):
        with open (playlist_file) as IN:
            playlist_details = json.load(IN)
            return playlist_details
    # If here, we must extract the full playlist and cache it
    result = dict()
    streamlit.write(f"Caching artist albums {artist_id}")
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?limit=50"
    print (url)
    response = requests.get(url, headers=headers)
    print (f"done {response.status_code}")
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        raise RuntimeError(f"Problem getting top albums for {artist_id}")
    jsondata = response.json()
    items = jsondata["items"]
    for item in items:
        result[item['id']] = item
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(result, indent=4))
    return result

def get_album_tracks(headers, album_id, ignore_cache=False):
    """Gets list of tracks from album"""
    playlist_file = ALBUM_TRACKS_CACHE_DIR + album_id + ".json"
    if not ignore_cache and os.path.exists(playlist_file):
        with open (playlist_file) as IN:
            playlist_details = json.load(IN)
            return playlist_details
    # If here, we must extract the full playlist and cache it
    streamlit.write(f"Caching album tracks for {album_id}")
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?limit=50"
    # url = f"https://api.spotify.com/v1/search?fear+artist:{artist_id}"
    print (url)
    response = requests.get(url, headers=headers)
    print (f"done {response.status_code}")
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        raise RuntimeError(f"Problem getting  tracks for album {album_id}")
    jsondata = response.json()
    itemlist = jsondata["items"]
    result=dict()
    for item in itemlist:
        result[item['id']] = item
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(result, indent=4))
    return result

def get_artist_all_tracks(headers, artist_id, ignore_cache=False):
    """Gets all tracks from all albums for given artist from cache or from the API."""
    playlist_file = ARTIST_ALL_TRACKS_CACHE_DIR + artist_id + ".json"
    # if not ignore_cache and os.path.exists(playlist_file):
    #     with open (playlist_file) as IN:
    #         playlist_details = json.load(IN)
    #         return playlist_details
    # If here, we must extract the full playlist and cache it
    streamlit.write(f"Caching artist total tracks for {artist_id}")
    albums = get_artist_albums(headers, artist_id, ignore_cache=ignore_cache)
    all_tracks = dict()
    for albumid in albums.keys():
        album_tracks = get_album_tracks(headers, albumid, ignore_cache=ignore_cache)
        for trackid in album_tracks.keys():
            track_metadata = album_tracks[trackid]
            artists = track_metadata.get("artists",[])
            for artist in artists:
                if artist["id"] == artist_id:
                    all_tracks[trackid] = album_tracks[trackid]
    with open(playlist_file, 'w') as OUT:
        OUT.write(json.dumps(all_tracks, indent=4))
    return all_tracks
