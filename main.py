from scripts.model1_scripts.embeddings import TitleEmbeddingModel
from pymilvus import connections, Collection


class Title2Playlist():

    def __init__(self, max_seq_length=30):
        connections.connect("default", host="localhost", port="19530")
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

    def create_playlist(self, title: str):
        title_embedding = self.embed_model([title], self.max_seq_length).flatten().tolist()
        nearest_playlists = self.find_nearest_playlists(title_embedding, 20)
        print(nearest_playlists)


if __name__ == "__main__":
    t2p = Title2Playlist()
    # t2p.create_playlist("top hits")
    # t2p.create_playlist("sad bops")
    # t2p.create_playlist("country wedding playlist")
    # t2p.create_playlist("head banger city")
    while True:
        title = input(">> ")
        t2p.create_playlist(title)
