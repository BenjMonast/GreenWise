from flask import Flask, request, render_template
from tokens import *
import base64, requests, re, pickle

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/carbon")
# def carbon():
#     return render_template("carbon.html")

@app.route("/manual")
def manual():
    return render_template("manual.html")


@app.route("/read_receipt", methods=['POST'])
def read_receipt():
    file = request.files['file']
    base64_image = base64.b64encode(file.read()).decode('utf-8')

    csv_text = None

    url = "https://api.taggun.io/api/receipt/v1/verbose/encoded"

    payload = {
        "image": base64_image,
        "filename": "image.jpg",
        "contentType": "image/jpeg"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apikey": TAGGUN_TOKEN
    }

    response = requests.post(url, json=payload, headers=headers)

    items = []

    for row in response.json()['amounts']:
        text = row['text']
        words = text.split(" ")
        if not (words[0].isnumeric() and len(words[0]) == 9):
            continue

        items.append((words[0], words[-1]))

    with open('redcircle_cache.pkl', 'rb') as f:
        cache = pickle.load(f)
    
    out = []

    for row in items:
        id = row[0]
        if id not in cache:
            json = requests.get(f"https://api.redcircleapi.com/request?api_key={RC_TOKEN}&type=search&search_term={id}").json()
            if "search_results" in json:
                cache[id] = json["search_results"]
            else:
                cache[id] = None

        if cache[id] == None:
            continue

        out.append([cache[id][0]['product']['title'], row[1]])

    with open('redcircle_cache.pkl', 'wb') as f:
        pickle.dump(cache, f)


    with open("db.pkl", "wb") as cache_file:
        pickle.dump(out, cache_file)
        
    return {"content": out}


if __name__ == '__main__':
    app.run()
