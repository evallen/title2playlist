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
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from tqdm import tqdm
import time
import os

# --- Parameters ---------------------------------------------------------------------------------------

ROOT_PATH = "."
ORIGINAL_SONG_DATASET_PATH = f"{ROOT_PATH}/data/song/song_dataset_1M_original.csv"
NEW_SONG_DATASET_PATH = f"{ROOT_PATH}/data/song/song_dataset.db"
PLAYLIST_DATASET_PATH = f"{ROOT_PATH}/data/playlist/data/"
SPOTIFY_MAX_TRACKS_PER_QUERY = 100

load_dotenv(f'{ROOT_PATH}/.env')
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())


# --- Functions ----------------------------------------------------------------------------------------

def table_exists(connection: sqlite3.Connection, name: str):
    """Return true if a given table exists."""
    cursor = connection.cursor()
    return cursor.execute(f"SELECT name FROM sqlite_master WHERE name='{name}'").fetchone() \
        is not None


# Initialize SQL table if not already exists
def initialize_db(connection: sqlite3.Connection):
    """Initialize the song database."""
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE songs(
        id                  TEXT        PRIMARY KEY,
        name                TEXT        NOT NULL,
        album               TEXT        NOT NULL,
        album_id            TEXT        NOT NULL,
        artists             TEXT        NOT NULL,
        artist_ids          TEXT        NOT NULL,
        acousticness        REAL        NOT NULL,
        danceability        REAL        NOT NULL,
        duration_ms         INTEGER     NOT NULL,
        energy              REAL        NOT NULL,
        instrumentalness    REAL        NOT NULL,
        key                 INTEGER     NOT NULL,
        liveness            REAL        NOT NULL,
        loudness            REAL        NOT NULL,
        mode                INTEGER     NOT NULL,
        speechiness         REAL        NOT NULL,
        tempo               REAL        NOT NULL,
        time_signature      REAL       NOT NULL,
        valence             REAL        NOT NULL
    )""")

    orig_song_ds_sliced = orig_song_ds[[
        'id', 'name', 'album', 'album_id', 'artists',
        'artist_ids', 'acousticness', 'danceability',
        'duration_ms', 'energy', 'instrumentalness', 'key',
        'liveness', 'loudness', 'mode', 'speechiness', 'tempo',
        'time_signature', 'valence'
    ]]
    orig_song_ds_sliced.to_sql(
        "songs", 
        connection, 
        if_exists="append",
        index=False
    )

    connection.commit()


def id_from_uri(uri: str):
    """Helper method to get the ID from a URI string like so:
    URI: 'spotify:artist:012345...'
    ID: '012345...'
    """
    return uri.split(':')[2]


def is_track_in_db(id, connection: sqlite3.Connection):
    """Find if a given track ID is in the database."""
    cursor = connection.cursor()
    return cursor.execute("SELECT EXISTS(SELECT 1 FROM songs WHERE id=(?))", [id]).fetchone()[0] == 1


def download_song_set(to_download, connection: sqlite3.Connection):
    """Download audio features for a set of songs to the database.
    `to_download` should be a dictionary whose keys are the IDs of the tracks
    to download and whose values are the full JSON of those tracks from the 
    playlsit database."""
    assert len(to_download) <= SPOTIFY_MAX_TRACKS_PER_QUERY
    assert len(to_download) > 0
    cursor = connection.cursor()

    to_download_id_list = list(to_download.keys())
    results = spotify.audio_features(to_download_id_list)

    # WARNING: It is possible some of these results come back as None because
    # audio features are not calculated yet for them (for some reason ?). 
    song_tuples = [(
            result['id'],

            # Track metadata not in audio features; must get from playlist
            # JSON. Sometimes we have to convert URIs ('spotify:track:0e9hR1...')
            # to IDs ('0e9hR1...'), and the database currently stores artist names
            # / IDs as a list in case there are multiple (['Justin Bieber', ...]) 
            # so we have to make sure we format our entries accordingly.
            to_download[result['id']]['track_name'],
            to_download[result['id']]['album_name'],
            id_from_uri(to_download[result['id']]['album_uri']),
            [to_download[result['id']]['artist_name']].__str__(),  # Must be list
            [id_from_uri(to_download[result['id']]['artist_uri'])].__str__(),  # Must be list

            result['acousticness'],
            result['danceability'],
            result['duration_ms'],
            result['energy'],
            result['instrumentalness'],
            result['key'],
            result['liveness'],
            result['loudness'],
            result['mode'],
            result['speechiness'],
            result['tempo'],
            result['time_signature'],
            result['valence'],
    ) for result in results if result is not None]

    cursor.executemany("""
    INSERT OR IGNORE INTO songs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, song_tuples)


def process_track(track_json, connection: sqlite3.Connection, to_download):
    """Process a given track's JSON by checking if we have it already and queuing it
    to be downloaded if not."""
    id = id_from_uri(track_json['track_uri'])

    if not is_track_in_db(id, connection):
        to_download[id] = track_json

        if len(to_download) == SPOTIFY_MAX_TRACKS_PER_QUERY:
            download_song_set(to_download, connection)
            to_download.clear()


def process_playlist_slice(slice_file_name: str, connection: sqlite3.Connection, pbar: tqdm):
    """Process a playlist slice file containing 1000 playlists.
    We provide the progress bar so we can update it with progress."""
    slice_file_path = f"{PLAYLIST_DATASET_PATH}/{slice_file_name}"

    with open(slice_file_path, 'r') as fd:
        slice_json = json.load(fd)

    to_download = {}

    for playlist in slice_json['playlists']:
        for track in playlist['tracks']:
            process_track(track, connection, to_download)
        pbar.update(1)
    
    if len(to_download) > 0:
        download_song_set(to_download, connection)
    
    connection.commit()


# --- MAIN ------------------------------------------------------------------------------------

if __name__ == "__main__":
    orig_song_ds = pd.read_csv(ORIGINAL_SONG_DATASET_PATH)
    connection = sqlite3.connect(NEW_SONG_DATASET_PATH)

    if not table_exists(connection, 'songs'):
        print("Initializing song database from CSV...")
        before = time.time()
        initialize_db(connection)
        print(f"Done initializing song database from CSV ({time.time() - before}s)")
    else:
        print("Song database already exists, continuing...")

    files = sorted(os.listdir(PLAYLIST_DATASET_PATH))

    with tqdm(total=1e6) as pbar:
        for file in files:
            process_playlist_slice(file, connection, pbar)



