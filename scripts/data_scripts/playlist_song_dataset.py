# # Song Dataset Creation
# 
# This script creates the full song dataset.
# 
# It starts from an initial song dataset downloaded from the internet and fills
# in whatever songs it doesn't have from the playlist dataset list.
# 
# Each song is queried from the Spotify API to get its features and other
# relevant information.

import pandas as pd
import sqlite3
import json
from dotenv import load_dotenv
from tqdm import tqdm
import time
import os
# --- Parameters ---------------------------------------------------------------------------------------

ROOT_PATH = "../.."
NEW_PLAYLIST_DATASET_PATH = f"{ROOT_PATH}/data/song/playlist_song.db"
PLAYLIST_DATASET_PATH = f"{ROOT_PATH}/data/playlist/"
def table_exists(connection: sqlite3.Connection, name: str):
    """Return true if a given table exists."""
    cursor = connection.cursor()
    return cursor.execute(f"SELECT name FROM sqlite_master WHERE name='{name}'").fetchone() \
        is not None

def id_from_uri(uri: str):
    """Helper method to get the ID from a URI string like so:
    URI: 'spotify:artist:012345...'
    ID: '012345...'
    """
    return uri.split(':')[2]
# Initialize SQL table if not already exists
def initialize_db(connection: sqlite3.Connection):
    """Initialize the song database."""
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE songs(
        playlistName        TEXT        NOT NULL,
        playlistID          TEXT        NOT NULL,
        songName            TEXT        NOT NULL,   
        songID              TEXT        NOT NULL,
        albumName           TEXT        NOT NULL,
        albumID             TEXT        NOT NULL,
        artistName          TEXT        NOT NULL,
        artistID            TEXT        NOT NULL,
        duration            INTEGER     NOT NULL
    )""")

    cursor.execute("CREATE INDEX pid_idx ON songs (playlistID)")

    connection.commit()

def process_playlist_slice(slice_file_name: str, connection: sqlite3.Connection, pbar: tqdm):
    """Process a playlist slice file containing 1000 playlists.
    We provide the progress bar so we can update it with progress."""
    slice_file_path = f"{PLAYLIST_DATASET_PATH}/{slice_file_name}"
    cursor = connection.cursor()
    with open(slice_file_path, 'r') as fd:
        slice_json = json.load(fd)

    for playlist in slice_json['playlists']:
        playlistName = playlist['name']
        playlistID = playlist['pid']
        for track in playlist['tracks']:
            songName = track['track_name']
            songID = id_from_uri(track['track_uri'])
            albumName = track['album_name']
            albumID = id_from_uri(track['album_uri'])
            artistName = track['artist_name']
            artistID = id_from_uri(track['artist_uri'])
            duration = track['duration_ms']
            song_tuple = (playlistName, playlistID, songName, songID, albumName, albumID, artistName, artistID, duration)
            cursor.execute("""INSERT INTO songs VALUES(?,?,?,?,?,?,?,?,?)""", song_tuple)
    connection.commit()
# --- MAIN ------------------------------------------------------------------------------------

if __name__ == "__main__":
    connection = sqlite3.connect(NEW_PLAYLIST_DATASET_PATH)

    if not table_exists(connection, 'songs'):
        print("Initializing playlist_song database from JSON")
        before = time.time()
        initialize_db(connection)
        print(f"Done initializing song database from JSON ({time.time() - before}s)")
    else:
        print("Song database already exists, continuing...")

    files = sorted(os.listdir(PLAYLIST_DATASET_PATH))
    
    with tqdm(total=1e6) as pbar:
        for file in files:
            process_playlist_slice(file, connection, pbar)
