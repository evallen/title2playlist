from sklearn.metrics import dcg_score
import numpy as np
import time


def evaluate_rankings(playlist, ranked_songs):
    """Evaluates a ranked set of songs against a playlist.
    
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


if __name__ == "__main__":
    assert_almost_equal(evaluate_rankings(['a', 'b', 'c'], ['b', 'd', 'e', 'c']), 0.671)
    assert_almost_equal(evaluate_rankings(['a', 'b', 'c'], ['a', 'b', 'c', 'd']), 1.0)
    assert_almost_equal(evaluate_rankings(['a', 'b', 'c'], ['d', 'a', 'b', 'c']), 0.733)
    print('OK')

    print('Running large benchmark')

    test_array = np.arange(24000)
    np.random.shuffle(test_array)

    then = time.time()
    assert_almost_equal(evaluate_rankings(test_array, test_array), 1.0)
    print(f"Time for 24000 entries: {time.time() - then}")




