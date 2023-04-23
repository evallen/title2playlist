from scripts.model1_scripts.embeddings import TitleEmbeddingModel
from pymilvus import connections, Collection
from scripts.model2_scripts.find_songsV2 import generate_songs
import sqlite3
import pandas as pd


class Title2Playlist():

    def __init__(self, song_db_path, max_seq_length=30):
        connections.connect("default", host="localhost", port="19530")
        self.song_conn = sqlite3.connect(song_db_path)
        self.collection = Collection("playlists")
        self.collection.load()
        self.embed_model = TitleEmbeddingModel('bert-base-cased')
        self.max_seq_length = max_seq_length
    
    def find_nearest_playlists(self, embedding, k):
        vectors_to_search = [embedding]
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        result = self.collection.search(vectors_to_search, "embedding", search_params, limit=k, output_fields=["pid", "title"])
        return result[0]

    def create_playlist(self, title: str, k):
        title_embedding = self.embed_model([title], self.max_seq_length).flatten().tolist()
        nearest_playlists = self.find_nearest_playlists(title_embedding, 300)
        nearest_ids = [playlist.entity.pid for playlist in nearest_playlists]
        nearest_titles = [playlist.entity.title for playlist in nearest_playlists]
        # for playlist in nearest_playlists:
        #     print(f"{playlist.distance}\t{playlist.entity.title}")
        return generate_songs(nearest_ids, k, self.song_conn)


if __name__ == "__main__":
    t2p = Title2Playlist("data/song/playlist_song.db")
    # t2p.create_playlist("top hits")
    # t2p.create_playlist("sad bops")
    # t2p.create_playlist("country wedding playlist")
    # t2p.create_playlist("head banger city")
    song_conn = sqlite3.connect("data/song/playlist_song.db")
    while True:
        title = input(">> ")
        songs = t2p.create_playlist(title, 10)
        for i, song in enumerate(songs):
            songQuery = f"SELECT * FROM songs WHERE songID = '{song}' LIMIT 1"
            topSongs = pd.read_sql(songQuery, song_conn)
            print(f"{i}: {topSongs['songName'].values.squeeze()} by {topSongs['artistName'].values.squeeze()} (from {topSongs['playlistName'].values.squeeze()})")
