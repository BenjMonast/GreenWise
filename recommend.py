from typing import List
import numpy as np
import pandas as pd
import pickle

from openai import OpenAI
from scipy import spatial
from tokens import OPENAI

from database import db

client = OpenAI(api_key=OPENAI)

EMBEDDING_MODEL = "text-embedding-3-small"

# establish a cache of embeddings to avoid recomputing
# cache is a dict of tuples (text, model) -> embedding, saved as a pickle file

# set path to embedding cache
embedding_cache_path = "embeddings_cache.pkl"

# load the cache if it exists, and save a copy to disk
try:
    embedding_cache = pd.read_pickle(embedding_cache_path)
except FileNotFoundError:
    embedding_cache = {}
with open(embedding_cache_path, "wb") as embedding_cache_file:
    pickle.dump(embedding_cache, embedding_cache_file)

# define a function to retrieve embeddings from the cache if present, and otherwise request via the API
def embedding_from_string(
    string: str,
    model: str = EMBEDDING_MODEL,
    embedding_cache=embedding_cache
) -> list:
    """Return embedding of given string, using a cache to avoid recomputing."""
    if (string, model) not in embedding_cache.keys():
        print("embedding not found in cache, calculating...")
        embedding_cache[(string, model)] = get_embedding(string, model)
        with open(embedding_cache_path, "wb") as embedding_cache_file:
            pickle.dump(embedding_cache, embedding_cache_file)
    return embedding_cache[(string, model)]



def get_embedding(input: str, model=EMBEDDING_MODEL):
    # replace newlines, which can negatively affect performance.
    input = input.replace("\n", " ")
    response = client.embeddings.create(
        input=input,
        model=model
    )
    return response.data[0].embedding


def distances_from_embeddings(
    query_embedding: List[float],
    embeddings: List[List[float]],
    distance_metric="cosine",
) -> List[List]:
    """Return the distances between a query embedding and a list of embeddings."""
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    distances = [
        distance_metrics[distance_metric](query_embedding, embedding)
        for embedding in embeddings
    ]
    return distances



def nearest_strings(
    strings: list[str],
    index_of_source_string: int,
    model=EMBEDDING_MODEL,
) -> list[int]:
    """Print out the k nearest neighbors of a given string."""
    # get embeddings for all strings
    embeddings = [embedding_from_string(string, model=model) for string in strings]

    # get the embedding of the source string
    query_embedding = embeddings[index_of_source_string]

    # get distances between the source embedding and other embeddings
    distances = distances_from_embeddings(query_embedding, embeddings, distance_metric="cosine")
    
    # get indices of nearest neighbors
    indices_of_nearest_neighbors = np.argsort(distances)

    return indices_of_nearest_neighbors, distances


if __name__ == '__main__':
    
    query_idx = 35
    query_string = db[query_idx, 0]

    indices_of_nearest_neighbors, distances = nearest_strings(db[:, 0], query_idx)

    count = 0
    for i in indices_of_nearest_neighbors:
        
        # skip any strings that are identical matches to the starting string
        if query_string == db[i, 0]:
            continue
        
        # stop after exceeding threshold
        if distances[i] > 0.6:
            break

        count += 1

        # print out the similar strings and their distances
        print(
            f"""
        --- Recommendation #{count} ---
        String: {db[i, 0]}
        Distance: {distances[i]:0.3f}"""
        )