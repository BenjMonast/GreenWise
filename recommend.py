from typing import List
import numpy as np
from numpy import genfromtxt
import pandas as pd
import pickle

from openai import OpenAI
from scipy import spatial
from tokens import OAI_TOKEN

client = OpenAI(api_key=OAI_TOKEN)

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

data = []
with open("carbon_cloud_data.csv", "r") as f:
    for line in f.readlines():
        line = line.split("|")
        line[2] = float(line[2])
        data.append(line)
db = np.array(data)


# define a function to retrieve embeddings from the cache if present, and otherwise request via the API
def get_embedding(
    string: str,
    model: str = EMBEDDING_MODEL,
    embedding_cache=embedding_cache
) -> list:
    """Return embedding of given string, using a cache to avoid recomputing."""
    if (string, model) not in embedding_cache.keys():
        # print("embedding not found in cache, calculating...")
        embedding_cache[(string, model)] = RAW_get_embedding(string, model)
        with open(embedding_cache_path, "wb") as embedding_cache_file:
            pickle.dump(embedding_cache, embedding_cache_file)
    return embedding_cache[(string, model)]



def RAW_get_embedding(input: str, model=EMBEDDING_MODEL):
    # replace newlines, which can negatively affect performance.
    input = input.replace("\n", " ")
    response = client.embeddings.create(
        input=input,
        model=model
    )
    return response.data[0].embedding
   
changed = False   
 
for i, row in enumerate(db):
    if (row[0], EMBEDDING_MODEL) not in embedding_cache:
        changed = True
        
        embedding_cache[(row[0], EMBEDDING_MODEL)] = RAW_get_embedding(row[0], EMBEDDING_MODEL)
        
        if i != 0 and i % 500 == 0:
            print("progress saved " + str(i))
            with open(embedding_cache_path, "wb") as embedding_cache_file:
                pickle.dump(embedding_cache, embedding_cache_file)
        
if changed:
    with open(embedding_cache_path, "wb") as embedding_cache_file:
        pickle.dump(embedding_cache, embedding_cache_file)


def distances_from_embeddings(query_embedding: List[float], embeddings: List[List[float]]) -> list[float]:
    """Return the distances between a query embedding and a list of embeddings."""
    distances = [spatial.distance.cosine(query_embedding, embedding) for embedding in embeddings]
    return distances



def nearest_strings(
    strings: list[str],
    query_string: str,
    model=EMBEDDING_MODEL,
) -> tuple[list[int], list[float]]:
    """Print out the k nearest neighbors of a given string."""
    # get embeddings for all strings
    embeddings = [get_embedding(string, model=model) for string in strings]

    # get the embedding of the source string
    query_embedding = get_embedding(query_string)

    # get distances between the source embedding and other embeddings
    distances = distances_from_embeddings(query_embedding, embeddings)
    
    # get indices of nearest neighbors
    indices_of_nearest_neighbors = np.argsort(distances)

    return indices_of_nearest_neighbors, distances

def get_c02e(prod: str, same_threshold=0.2):
    cmp_strs = np.char.lower(db[:, 0])

    if prod.lower() in cmp_strs:
        for item in db:
            if np.char.lower(item[0]) == prod.lower():
                return item[2]
    else:
        _, distances = nearest_strings(db[:, 0], prod)
        really_close = [float(db[i, 2]) for i, d in enumerate(distances) if d <= same_threshold]
        if len(really_close) > 0:
            return sum(really_close) / len(really_close)
        else:
            print("UNABLE TO FIND SIMILIAR ITEMS....")
            return -1



def get_rec(prod: str, rank_threshold=0.4, same_threshold=0.2, exclude_high_carbon=True):

    indices_of_nearest_neighbors, distances = nearest_strings(db[:, 0], prod)

    carbon_cost = get_c02e(prod, same_threshold)

    ranks = []
    for i in indices_of_nearest_neighbors:
        
        # skip any strings that are identical matches to the starting string
        if prod == db[i, 0]:
            continue
        
        # stop after exceeding threshold
        if distances[i] > rank_threshold:
            break

        if exclude_high_carbon and carbon_cost <= float(db[i, 2]):
            break

        ranks.append(i)

    return db[ranks]



if __name__ == '__main__':
    
    # query_string = db[35, 0]
    query_string = "Frosted Cereal"

    carbon_cost = get_c02e(query_string)
    print(f"Finding alternatives for: {query_string}   (C02e cost: {carbon_cost})")

    for count, rec in enumerate(get_rec(query_string, rank_threshold=0.6, exclude_high_carbon=False)):

        isLowCarbonStr = "LOWER CARBON" if float(rec[2]) < carbon_cost else ""

        # print out the similar strings and their distances
        print(
            f"""
        --- {isLowCarbonStr} Recommendation #{count + 1} ---
        String: {rec[0]}
        C02e: {rec[2]}"""
        )