from sklearn.metrics import dcg_score
import numpy as np
import time


def indexes(playlist, ranked_songs):
    indexes = []
    for song in playlist:
        try:
            indexes.append(ranked_songs.index(song))
        except ValueError:
            pass

    return indexes


def num_found(playlist, ranked_songs, k=None):
    """Finds the number of songs from the actual
    playlist that are in the ranked songs list, up to
    element k if provided.
    
    Params:
    - playlist: A list of song IDs representing songs in a real playlist.
    - ranked_songs: An (ordered) list of IDs representing songs returned
                    by our algorithm. The most relevant songs are on the top.
    - k: How many ranked_songs to look through. If None, all of them.

    Returns:
    - How many real playlist songs are in the ranked songs list
      up to element k.
    """
    if k is None:
        search_songs = ranked_songs
    else: 
        search_songs = ranked_songs[:k]

    return sum([1 if song in search_songs else 0 for song in playlist])


def recall_k(playlist, ranked_songs, k):
    """Recall@k: Finds the percentage of songs from the actual
    playlist that are in the first k entries of the ranked_songs list.

    Params:
    - playlist: A list of song IDs representing songs in a real playlist.
    - ranked_songs: An (ordered) list of IDs representing songs returned
                    by our algorithm. The most relevant songs are on the top.
    - k: How many ranked_songs to look through.
    
    Returns:
    - The percentage of songs in the real playlist that are in the
      ranked songs list up to element k.
    """
    return num_found(playlist, ranked_songs, k) / len(playlist)


def r_precision(playlist_tuples, ranked_songs_tuples):
    """R-precision: Finds the percentage of songs from the actual
    playlist that are in the first n entries of the ranked_songs list,
    where n is the number of songs in the actual playlist. Adds 
    a bonus for getting the artist right.
    
    The formula (from Spotify) is:
    
    r_precision = |St & Gt| + 0.25 * |Sa & Ga|
                  ----------------------------
                             |Gt|
    
    where
        Gt, Ga are the ground truth track IDs and artist IDs, and 
        St, Sa are the track IDs and artist IDs in the recommended songs, and
        & is the set intersection operator.
        Note that Gt, Ga, St, and Sa must all be the SAME length.
    
    Params:
    - playlist_tuples: A list of tuples (song_id, artist_id) for all the songs in the
                       real playlist
    - ranked_songs_tuples: A list of tuples (song_id, artist_id) for all the songs in 
                           the output playlist
    
    Returns:
    - The r-precision metric.
    """
    assert(len(playlist_tuples) == len(ranked_songs_tuples))

    playlist_song_ids, playlist_artist_ids = zip(*playlist_tuples)
    ranked_song_ids, ranked_artist_ids = zip(*ranked_songs_tuples)

    return recall_k(playlist_song_ids, ranked_song_ids, len(playlist_song_ids)) + \
           0.25 * recall_k(playlist_artist_ids, ranked_artist_ids, len(playlist_artist_ids))


def first_index(playlist, ranked_songs):
    """Finds the first index of a song from the real playlist
    in the ranked songs list.

    Params:
    - playlist: A list of song IDs representing songs in a real playlist.
    - ranked_songs: An (ordered) list of IDs representing songs returned
                    by our algorithm. The most relevant songs are on the top.
    
    Returns:
    - The index of the first song in the ranked list that appears in the 
      playlist.
    """
    first = len(ranked_songs)
    for song in playlist:
        try:
            idx = ranked_songs.index(song)
            first = min(first, idx)
        except ValueError:
            pass
    
    if first == len(ranked_songs):
        first = None

    return first


def ndcg(playlist, ranked_songs):
    """Evaluates a ranked set of songs against a playlist using NDCG.
    
    Params:
    - playlist: A list of song IDs representing songs in a real playlist.
    - ranked_songs: An (ordered) list of IDs representing songs returned
                    by our algorithm. The most relevant songs are on the top.
    
    Returns:
    - A version of the Normalized Discounted Cumulative Gain (NDCG) score
      of the ranked_songs list. Specifically, we compute the Discounted
      Cumulative Gain (DCG) as normal, but then we compute the Ideal
      Discounted Cumulative Gain (IDCG) differently by adding in any songs
      from `playlist` that weren't in `ranked_songs`.
      This penalizes the `ranked_songs` list for missing songs in `playlist`.
    """

    missing_songs = set(playlist) - set(ranked_songs)
    
    y_true = np.array([[1 if song in playlist else 0 for song in ranked_songs]])
    y_score = np.array([np.arange(len(ranked_songs)-1, -1, -1)])  # Reverse order
    dcg = dcg_score(y_true, y_score, ignore_ties=True)

    y_ideal = np.concatenate((y_true, np.ones((1,len(missing_songs)))), axis=1)
    idcg = dcg_score(y_ideal, y_ideal, ignore_ties=True)

    return dcg / idcg


def assert_almost_equal(a, b, delta=0.01):
    assert(a - b < delta)


def test_num_found():
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 1), 0)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 2), 0)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 3), 1)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 4), 2)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'a', 'b', 'c'], 4), 3)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'a', 'b', 'c']), 3)
    print('OK')


def test_recall_k():
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 1), 0)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 2), 0)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 3), 0.333)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'd', 'b', 'c'], 4), 0.666)
    assert_almost_equal(recall_k(['a', 'b', 'c'], ['e', 'a', 'b', 'c'], 4), 1)
    print('OK')


def test_r_precision():
    assert_almost_equal(r_precision([('a', 'A'), ('b', 'B'), ('c', 'C')], 
                                    [('a', 'A'), ('e', 'B'), ('f', 'F')]),
                                    0.5)
    print('OK')


def test_first_index():
    assert(first_index(['a', 'b', 'c'], ['e', 'd', 'b', 'c']) == 2)
    assert(first_index(['a', 'b', 'c'], ['a', 'b', 'c', 'd']) == 0)
    assert(first_index(['a', 'b', 'c'], ['d']*50 + ['a']) == 50)
    assert(first_index(['a', 'b', 'c'], ['d']) is None)
    print('OK')


def test_ndcg():
    assert_almost_equal(ndcg(['a', 'b', 'c'], ['b', 'd', 'e', 'c']), 0.671)
    assert_almost_equal(ndcg(['a', 'b', 'c'], ['a', 'b', 'c', 'd']), 1.0)
    assert_almost_equal(ndcg(['a', 'b', 'c'], ['d', 'a', 'b', 'c']), 0.733)
    print('OK')

    print('Running large benchmark')

    test_array = np.arange(24000)
    np.random.shuffle(test_array)

    then = time.time()
    assert_almost_equal(ndcg(test_array, test_array), 1.0)
    print(f"Time for 24000 entries: {time.time() - then}")


if __name__ == "__main__":
    test_ndcg()
    test_first_index()
    test_recall_k()
    test_r_precision()
