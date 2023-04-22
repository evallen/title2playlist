from pymilvus import (
    connections,
    FieldSchema,
    DataType,
    CollectionSchema,
    Collection,
    utility,
)
import json
import glob
import sys
sys.path.insert(0, '.')
from scripts.model1_scripts.embeddings import TitleEmbeddingModel
from tqdm import tqdm
import time


# --- Parameters ------------------------------------------------------------------

VEC_DIM = 768
MAX_TITLE_LEN = 200 
EMBEDDING_SEQ_LEN = 30
BATCH_SIZE = None
TEST_N = 3000
COLLECTION_NAME = "playlists"

FIELDS = [
    FieldSchema(name="pid", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=MAX_TITLE_LEN),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VEC_DIM)
]


# --- Helper functions ------------------------------------------------------------

def load_slice(collection, embedding_model, slice_path):
    # then = time.time()
    with open(slice_path) as fp:
        slice_json = json.load(fp)
    # print(f"JSON load: {time.time() - then}")
    
    # then = time.time()
    playlists = slice_json['playlists']
    pids = [playlist['pid'] for playlist in playlists]
    titles = [playlist['name'][:MAX_TITLE_LEN] for playlist in playlists]
    # print(f"Extract PIDs, titles: {time.time() - then}")

    # then = time.time()
    embeddings = embedding_model(titles, EMBEDDING_SEQ_LEN, batch_size=BATCH_SIZE)
    # print(f"Make embeddings: {time.time() - then}")

    # then = time.time()
    entities = [
        pids,
        titles,
        [embeddings[i].tolist() for i in range(embeddings.shape[0])]
    ]
    # print(F"Put together: {time.time() -then}")

    # then = time.time()
    collection.insert(entities)
    # print(f"Put into collection: {time.time() - then}")


def build_collection():
    schema = CollectionSchema(FIELDS, "Playlist embeddings")
    collection = Collection(COLLECTION_NAME, schema)
    embedding_model = TitleEmbeddingModel('bert-base-cased')

    print("Loading slices...")
    for slice_path in tqdm(sorted(glob.glob("./data/playlist/data/*.json"))):
        load_slice(collection, embedding_model, slice_path)
    
    collection.flush()
    print("Done loading slices.")
    print("Making index...")

    index = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128},
    }

    collection.create_index("embedding", index)

    print("Done making database.")


# --- Main ---------------------------------------------------------------------------
if __name__ == "__main__":
    connections.connect("default", host="localhost", port="19530")

    if not utility.has_collection(COLLECTION_NAME):
        print("Building new collection...")
        build_collection()
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists")


