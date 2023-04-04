# Title Dataset Creation
# 
# This script creates the full title dataset, pairing
# titles and song space representations. Each row of the dataset
# represents a single playlist, and the dataset has 
# 2d+1 columns, where d is the number of feature dimensions:
#   - 1 column for the title of the playlist
#   - 2 columns for each of d features: mean and variance
# 
# It uses the downloaded playlist dataset and the created song dataset
# from `create_song_dataset.py`.

import pandas as pd
import json
import sqlite3
from tqdm import tqdm
import os
import time

# --- Parameters ---------------------------------------------------------------------------------------

ROOT_PATH = "."
SONG_DATASET_PATH = f"{ROOT_PATH}/data/song/song_dataset.db"
PLAYLIST_DATASET_PATH = f"{ROOT_PATH}/data/playlist/data/"
TITLE_DATASET_DIR = f"{ROOT_PATH}/data/title/"
TITLE_DATASET_PATH = f"{TITLE_DATASET_DIR}/title_dataset.db"

# Removed 'key' because it's hard to interpret
FEATURE_NAMES = [
    "acousticness",
    "danceability",
    "duration_ms",
    "energy",
    "instrumentalness",
    "liveness",
    "loudness",
    "mode",
    "speechiness",
    "tempo",
    "time_signature",
    "valence"
]

TITLE_COLUMN_NAMES = \
    ["title"] + \
    [feature+"_mean" for feature in FEATURE_NAMES] + \
    [feature+"_sd" for feature in FEATURE_NAMES]

TITLE_SCHEMA =  \
"""CREATE TABLE titles(
    title                   TEXT        NOT NULL,
    acousticness_mean       REAL        NOT NULL,
    acousticness_sd         REAL        NOT NULL,
    danceability_mean       REAL        NOT NULL,
    danceability_sd         REAL        NOT NULL,
    duration_ms_mean        REAL        NOT NULL,
    duration_ms_sd          REAL        NOT NULL,
    energy_mean             REAL        NOT NULL,
    energy_sd               REAL        NOT NULL,
    instrumentalness_mean   REAL        NOT NULL,
    instrumentalness_sd     REAL        NOT NULL,
    liveness_mean           REAL        NOT NULL,
    liveness_sd             REAL        NOT NULL,
    loudness_mean           REAL        NOT NULL,
    loudness_sd             REAL        NOT NULL,
    mode_mean               REAL        NOT NULL,
    mode_sd                 REAL        NOT NULL,
    speechiness_mean        REAL        NOT NULL,
    speechiness_sd          REAL        NOT NULL,
    tempo_mean              REAL        NOT NULL,
    tempo_sd                REAL        NOT NULL,
    time_signature_mean     REAL        NOT NULL,
    time_signature_sd       REAL        NOT NULL,
    valence_mean            REAL        NOT NULL,
    valence_sd              REAL        NOT NULL
)"""

# --- Functions ----------------------------------------------------------------------------------------

def table_exists(connection: sqlite3.Connection, name: str):
    """Return true if a given table exists."""
    cursor = connection.cursor()
    return cursor.execute(f"SELECT name FROM sqlite_master WHERE name='{name}'").fetchone() \
        is not None


# Initialize SQL table if not already exists
def initialize_db(connection: sqlite3.Connection):
    """Initialize the title database."""
    cursor = connection.cursor()

    cursor.execute(TITLE_SCHEMA)


def id_from_uri(uri: str):
    """Helper method to get the ID from a URI string like so:
    URI: 'spotify:artist:012345...'
    ID: '012345...'
    """
    return uri.split(':')[2]


def process_playlist(playlist: dict, song_conn: sqlite3.Connection):
    """Process a single playlist from its JSON dictionary."""
    ids = [id_from_uri(track['track_uri']) for track in playlist['tracks']]

    # Queries for all the given songs. 
    # The interpolated bit expands to (?,?,?,?,...,?) for as many ids as we have,
    # so this is still a prepared statement and there is no SQL injection vulnerability.
    songs = pd.read_sql(
        "SELECT * FROM songs WHERE id IN ({0})".format(','.join('?' for _ in ids)),
        song_conn,
        params=ids,
    )

    means = songs[FEATURE_NAMES].mean(axis=0).add_suffix("_mean")
    sds = songs[FEATURE_NAMES].std(axis=0).add_suffix("_sd")

    playlist_df = pd.concat((means, sds), axis=0)
    playlist_df['title'] = playlist['name']
    return playlist_df
    

def process_playlist_slice(slice_file_name: str, title_conn: sqlite3.Connection, 
                           song_conn: sqlite3.Connection, pbar: tqdm):
    """Process a playlist slice file containing 1000 playlists.
    We provide the progress bar so we can update it with progress."""
    slice_file_path = f"{PLAYLIST_DATASET_PATH}/{slice_file_name}"

    with open(slice_file_path, 'r') as fd:
        slice_json = json.load(fd)

    overall_df = pd.DataFrame(columns=TITLE_COLUMN_NAMES)
    for playlist in slice_json['playlists']:
        playlist_row = process_playlist(playlist, song_conn)
        overall_df = pd.concat((overall_df, playlist_row.to_frame().T))
        pbar.update(1)
        
    before = time.time()
    # overall_df.to_sql('titles', title_conn, if_exists='append', index=False, method='multi')
    overall_df.to_sql('titles', title_conn, if_exists='append', index=False)
    print(f"Bulk SQL insert for slice: {time.time() - before}")


# --- MAIN ------------------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists(TITLE_DATASET_DIR):
        os.mkdir(TITLE_DATASET_DIR)

    title_conn = sqlite3.connect(TITLE_DATASET_PATH)
    song_conn = sqlite3.connect(SONG_DATASET_PATH)

    if not table_exists(title_conn, 'titles'):
        print("Initializing title database...")
        initialize_db(title_conn)
    else:
        print("Title database already exists, continuing...")

    files = sorted(os.listdir(PLAYLIST_DATASET_PATH))

    with tqdm(total=1e6) as pbar:
        for file in files:
            process_playlist_slice(file, title_conn, song_conn, pbar)



