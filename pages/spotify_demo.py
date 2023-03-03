import streamlit
import spotipy
import sys, os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT = os.environ["SPOTIFY_CLIENT"]
SPOTIFY_SECRET = os.environ["SPOTIFY_SECRET"]

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

myId = "12129890718"
me = sp.user(myId)
me

playlists = sp.user_playlists(myIdx)
playlists
while playlists:
    for i, playlist in enumerate(playlists['items']):
        print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None
playlists