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
        print("embedding not found in cache, calculating...")
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

embeds = []
names = []
ids = []
meta_data = []

for i, row in enumerate(db):

    if (row[0], EMBEDDING_MODEL) not in embedding_cache:
        print("REDO!!!!!!!!!!!!!!!")
        changed = True
        
        embedding_cache[(row[0], EMBEDDING_MODEL)] = RAW_get_embedding(row[0], EMBEDDING_MODEL)
        
        if i != 0 and i % 500 == 0:
            print("progress saved " + str(i))
            with open(embedding_cache_path, "wb") as embedding_cache_file:
                pickle.dump(embedding_cache, embedding_cache_file)

    embeds.append(embedding_cache[(row[0], EMBEDDING_MODEL)])
    names.append(row[0])
    ids.append(str(i))
    meta_data.append({"carbon": row[2], "company": row[1]})
        
if changed:
    with open(embedding_cache_path, "wb") as embedding_cache_file:
        pickle.dump(embedding_cache, embedding_cache_file)


import chromadb
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("test")

v = embedding_cache.values()

print("loading into chroma")

BATCH_SIZE = 5000

for i in range(0, len(embeds), BATCH_SIZE):
    collection.add(
        embeddings=embeds[i:min(i+BATCH_SIZE,len(embeds))],
        metadatas=meta_data[i:min(i+BATCH_SIZE,len(embeds))],
        documents=names[i:min(i+BATCH_SIZE,len(embeds))],
        ids=ids[i:min(i+BATCH_SIZE,len(embeds))],
    )

print("loaded chroma")
# res = collection.query(
#         query_embeddings=[RAW_get_embedding("Frosted Flakes")],
#         n_results=4,
#     )

# print(res)
# quit()

def nearest_strings(
    query_string: str,
    model=EMBEDDING_MODEL,
) -> tuple[list[int], list[float]]:
    """Print out the nearest neighbors of a given string."""

    # get the embedding of the source string
    query_embedding = get_embedding(query_string)

    # get distances between the source embedding and other embeddings
    res = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
    )

    print("="*8)
    print("SEARCHING: ", query_string)
    print("="*5)
    for i in range(len(res["documents"][0])): # 
        print(f"String: {res['documents'][0][i]}\nDistance:{res['distances'][0][i]}")
    print("="*8)

    return res["documents"][0], res["distances"][0], [float(c["carbon"]) for c in res["metadatas"][0]], [c["company"] for c in res["metadatas"][0]]


def get_co2e(prod: str, same_threshold=0.9):
    cmp_strs = np.char.lower(db[:, 0])

    if prod.lower() in cmp_strs:
        for item in db:
            if np.char.lower(item[0]) == prod.lower():
                return round(item[2],2)
    else:
        _, distances, co2e, _ = nearest_strings(prod)
        really_close = [co2e[i] for i, d in enumerate(distances) if d <= same_threshold]
        if len(really_close) > 0:
            return round(sum(really_close) / len(really_close),2)
        else:
            print("UNABLE TO FIND SIMILIAR ITEMS....")
            return -1



def get_rec(prod: str, rank_threshold=2.0, exclude_high_carbon=True):

    names, distances, carbon, companies = nearest_strings(prod)

    carbon_cost = get_co2e(prod)

    for i, name in enumerate(names):
        
        # skip any strings that are identical matches to the starting string
        if prod == name:
            continue
        
        # stop after exceeding threshold
        if distances[i] > rank_threshold:
            continue

        if exclude_high_carbon and carbon_cost <= carbon[i] + 0.05:
            continue

        return name, float(carbon[i]), distances[i], companies[i]

    return -1, -1, -1, -1


if __name__ == '__main__':
    
    # query_string = db[35, 0]
    query_string = "Frosted Cereal"

    carbon_cost = get_co2e(query_string)
    print(f"Finding alternatives for: {query_string}   (C02e cost: {carbon_cost})")

    rec_name, rec_carbon, rec_dist, rec_company = get_rec(query_string, rank_threshold=0.6, exclude_high_carbon=False)

    isLowCarbonStr = "LOWER CARBON" if rec_carbon < carbon_cost else ""

    # print out the similar strings and their distances
    print(
        f"""
    --- {isLowCarbonStr} Recommendation  ---
    String: {rec_name}
    Company: {rec_company}
    C02e: {rec_carbon}
    dist: {rec_dist}"""
    )